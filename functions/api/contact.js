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
  if (!env.ENQUIRY && !env.EMAIL) return reply(503, {error: 'This site is not configured to accept enquiries.'});
  let form;
  try { form = await request.formData(); } catch { return reply(400, {error: 'Submission could not be read.'}); }
  if (String(form.get('website') || '').trim()) return done(200, {ok: true}); // Honeypot: accept, discard.
  const enquiry = {};
  for (const [field, limit] of Object.entries(LIMITS)) {
    const value = String(form.get(field) || '').trim();
    if (!value && !OPTIONAL.has(field)) return reply(400, {error: `Missing required field: ${field}.`});
    if (value.length > limit) return reply(400, {error: `Field is too long: ${field}.`});
    enquiry[field] = value;
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(enquiry.email)) return reply(400, {error: 'Enter a valid email address.'});
  enquiry.received = new Date().toISOString();
  try {
    // The durable copy is written first, so a notification failure never loses an enquiry.
    if (env.ENQUIRY) await env.ENQUIRY.put(`enquiry:${enquiry.received}:${crypto.randomUUID()}`, JSON.stringify(enquiry));
    if (env.EMAIL) await env.EMAIL.send({
      to: env.ENQUIRY_TO, from: env.ENQUIRY_FROM, subject: 'Website enquiry',
      text: Object.entries(enquiry).map(([field, value]) => `${field}: ${value}`).join('\n'),
    });
  } catch (error) {
    if (!env.ENQUIRY) return reply(502, {error: 'Delivery could not be confirmed.'});
  }
  return done(200, {ok: true});
}
