// Cloudflare Pages Function: the contact form's only delivery path.
// ponytail: honeypot only, no Turnstile — Turnstile needs script-src/frame-src added to
// static/_headers, which weakens the CSP. Add it if spam actually arrives.
const LIMITS = {name: 120, email: 254, company: 160, 'project-type': 80, budget: 80, message: 5000};
const OPTIONAL = new Set(['company']);
const reply = (status, body) => new Response(JSON.stringify(body), {status, headers: {'content-type': 'application/json'}});

export async function onRequestPost({request, env}) {
  // A form posted without JavaScript expects a page, not JSON.
  const wantsPage = !(request.headers.get('accept') || '').includes('application/json');
  const done = (status, body) => wantsPage && status < 400
    ? Response.redirect(new URL('/contact/received/', request.url), 303)
    : reply(status, body);
  // Intake is an explicit per-deployment decision. Inherited bindings alone never open
  // this endpoint: ENQUIRY_ENABLED must be set to "true" for the deployment that owns them.
  const open = String(env.ENQUIRY_ENABLED || '').trim().toLowerCase() === 'true';
  if (!open || (!env.ENQUIRY && !env.NOTIFICATION_WEBHOOK)) return reply(503, {error: 'This site is not configured to accept enquiries.'});
  let form;
  try { form = await request.formData(); } catch { return reply(400, {error: 'Submission could not be read.'}); }
  if (String(form.get('website') || '').trim()) return done(200, {ok: true}); // Honeypot: accept, discard.

  // Best-effort IP-based rate limiting via KV (max 5 requests per 10-minute window).
  // Cloudflare KV is an eventually consistent store without distributed atomic increments;
  // this provides practical burst throttling against single-IP abuse rather than a strict mutex.
  const ip = request.headers.get('cf-connecting-ip') || '';
  if (ip && env.ENQUIRY && typeof env.ENQUIRY.get === 'function') {
    const rlKey = `ratelimit:${ip}`;
    try {
      const current = parseInt(await env.ENQUIRY.get(rlKey) || '0', 10);
      if (current >= 5) {
        return reply(429, {error: 'Too many enquiries submitted. Please wait before trying again.'});
      }
      await env.ENQUIRY.put(rlKey, String(current + 1), {expirationTtl: 600});
    } catch {
      // Best-effort rate limiting; do not block users if KV get fails
    }
  }

  const enquiry = {};
  for (const [field, limit] of Object.entries(LIMITS)) {
    const value = String(form.get(field) || '').trim();
    if (!value && !OPTIONAL.has(field)) return reply(400, {error: `Missing required field: ${field}.`});
    if (value.length > limit) return reply(400, {error: `${field} exceeds the maximum length of ${limit} characters.`});
    enquiry[field] = value;
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(enquiry.email)) return reply(400, {error: 'Enter a valid email address.'});
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
      return reply(502, {error: 'Your enquiry could not be stored, so it has not been received. Please try again.'});
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
          text: `New website enquiry from ${enquiry.name} (${enquiry.email}):\n${enquiry.message}`,
          enquiry,
        }),
      });
      webhookOk = res && res.ok;
    } catch {
      webhookOk = false;
    }
    if (!webhookOk && !stored) {
      return reply(502, {error: 'Delivery could not be confirmed.'});
    }
  }
  return done(200, {ok: true});
}
