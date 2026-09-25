// Cloudflare Pages Function: the contact form's only delivery path.
// ponytail: honeypot only, no Turnstile — Turnstile needs script-src/frame-src added to
// static/_headers, which weakens the CSP. Add it if spam actually arrives.
const LIMITS = {name: 120, email: 254, company: 160, 'project-type': 80, budget: 80, message: 5000};
const OPTIONAL = new Set(['company']);
const ALLOWED_FIELDS = new Set(['name', 'email', 'company', 'project-type', 'budget', 'message', 'website']);
const MAX_BODY_BYTES = 65536;
const reply = (status, body) => new Response(JSON.stringify(body), {status, headers: {'content-type': 'application/json', 'cache-control': 'no-store'}});
const escapeHTML = text => String(text).replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
// A visitor without JavaScript sees this instead of raw JSON. No inline style or script, so
// the strict CSP in static/_headers still applies.
const errorPage = (status, message) => new Response(`<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>Your enquiry was not sent</title></head>
<body><main><h1>Your enquiry was not sent</h1><p>${escapeHTML(message)}</p>
<p><a href="/contact/">Go back to the contact form</a></p></main></body></html>
`, {status, headers: {'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store'}});
// Chat tools read webhook text as markup: <!channel> or @here would ping a whole team.
const chatSafe = text => String(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/@/g, '@\u200b');
// Rate-limit keys hold a hash, never the raw address. Set RATE_LIMIT_SALT as a secret so the
// hash cannot be reversed by trying every address.
const ipKey = async (ip, salt) => {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(`${salt || 'enquiry-rate-limit'}:${ip}`));
  return [...new Uint8Array(digest)].slice(0, 16).map(b => b.toString(16).padStart(2, '0')).join('');
};

export async function onRequestPost({request, env}) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({error: 'Method Not Allowed'}), {
      status: 405,
      headers: {'allow': 'POST', 'content-type': 'application/json', 'cache-control': 'no-store'},
    });
  }
  // A form posted without JavaScript expects a page, not JSON.
  const wantsPage = !(request.headers.get('accept') || '').includes('application/json');
  const done = (status, body) => {
    if (!wantsPage) return reply(status, body);
    return status < 400 ? Response.redirect(new URL('/contact/received/', request.url), 303) : errorPage(status, body.error);
  };

  const contentType = (request.headers.get('content-type') || '').toLowerCase();
  if (!contentType.includes('application/x-www-form-urlencoded') && !contentType.includes('multipart/form-data')) {
    return done(415, {error: 'Unsupported content type. Expected form submission.'});
  }

  const contentLength = parseInt(request.headers.get('content-length') || '0', 10);
  if (contentLength > MAX_BODY_BYTES) {
    return done(413, {error: 'Payload too large.'});
  }

  // Intake is an explicit per-deployment decision. Inherited bindings alone never open
  // this endpoint: ENQUIRY_ENABLED must be set to "true" for the deployment that owns them.
  const open = String(env.ENQUIRY_ENABLED || '').trim().toLowerCase() === 'true';
  if (!open || (!env.ENQUIRY && !env.NOTIFICATION_WEBHOOK)) return done(503, {error: 'This site is not configured to accept enquiries.'});
  // Browsers send Origin with a form POST. One from another website is not our form.
  const origin = request.headers.get('origin');
  if (origin && origin !== new URL(request.url).origin) return done(403, {error: 'Enquiries must be sent from this website.'});
  let form;
  try { form = await request.formData(); } catch { return done(400, {error: 'Submission could not be read.'}); }

  const seen = new Set();
  for (const [key, value] of form.entries()) {
    if (!ALLOWED_FIELDS.has(key)) {
      return done(400, {error: `Unexpected field: ${key}.`});
    }
    if (seen.has(key)) {
      return done(400, {error: `Duplicate field: ${key}.`});
    }
    seen.add(key);
    if (typeof value !== 'string') {
      return done(400, {error: `File uploads are not accepted for ${key}.`});
    }
  }

  if (String(form.get('website') || '').trim()) return done(200, {ok: true}); // Honeypot: accept, discard.

  // Best-effort IP-based rate limiting via KV (max 5 requests per 10-minute window).
  // Cloudflare KV is an eventually consistent store without distributed atomic increments;
  // this provides practical burst throttling against single-IP abuse rather than a strict mutex.
  // An optional RATE_LIMIT namespace keeps these counters out of the enquiry store.
  const ip = request.headers.get('cf-connecting-ip') || '';
  const limiter = env.RATE_LIMIT || env.ENQUIRY;
  if (ip && limiter && typeof limiter.get === 'function') {
    try {
      const rlKey = `ratelimit:${await ipKey(ip, env.RATE_LIMIT_SALT)}`;
      const current = parseInt(await limiter.get(rlKey) || '0', 10);
      if (current >= 5) {
        return done(429, {error: 'Too many enquiries submitted. Please wait before trying again.'});
      }
      await limiter.put(rlKey, String(current + 1), {expirationTtl: 600});
    } catch {
      // Best-effort rate limiting; do not block users if KV get fails
    }
  }

  const enquiry = {};
  for (const [field, limit] of Object.entries(LIMITS)) {
    const value = String(form.get(field) || '').trim();
    if (!value && !OPTIONAL.has(field)) return done(400, {error: `Missing required field: ${field}.`});
    if (value.length > limit) return done(400, {error: `${field} exceeds the maximum length of ${limit} characters.`});
    enquiry[field] = value;
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(enquiry.email)) return done(400, {error: 'Enter a valid email address.'});
  enquiry.received = new Date().toISOString();
  // The durable copy is the receipt: nothing is acknowledged until the write succeeds.
  // 90-day retention prevents indefinitely hoarding personal data in KV.
  let stored = false;
  if (env.ENQUIRY) {
    try {
      const TTL_SECONDS = 90 * 24 * 60 * 60; // 90 days
      await env.ENQUIRY.put(`enquiry:${enquiry.received}:${crypto.randomUUID()}`, JSON.stringify(enquiry), {expirationTtl: TTL_SECONDS});
      stored = true;
    } catch {
      return done(502, {error: 'Your enquiry could not be stored, so it has not been received. Please try again.'});
    }
  }
  // Webhook notification: best effort once a copy is stored, and the only delivery path
  // when no store is bound. Pages Functions cannot bind send_email, so there is no email path.
  if (env.NOTIFICATION_WEBHOOK) {
    let webhookOk = false;
    try {
      const res = await fetch(env.NOTIFICATION_WEBHOOK, {
        method: 'POST',
        signal: AbortSignal.timeout(10000),
        headers: {'content-type': 'application/json'},
        body: JSON.stringify({
          text: chatSafe(`New website enquiry from ${enquiry.name} (${enquiry.email}):\n${enquiry.message}`),
          enquiry,
        }),
      });
      webhookOk = res && res.ok;
    } catch {
      webhookOk = false;
    }
    if (!webhookOk && !stored) {
      return done(502, {error: 'Delivery could not be confirmed.'});
    }
  }
  return done(200, {ok: true});
}

export async function onRequest(context) {
  if (context.request.method === 'POST') {
    return onRequestPost(context);
  }
  return new Response(JSON.stringify({error: 'Method Not Allowed'}), {
    status: 405,
    headers: {'allow': 'POST', 'content-type': 'application/json', 'cache-control': 'no-store'},
  });
}
