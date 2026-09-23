/* Failure-path checks for the contact Pages Function, with no network or Cloudflare account.
   The endpoint is called directly with stub bindings; check_contact.sh covers the real ones. */
import assert from 'node:assert/strict';
import {onRequestPost} from '../functions/api/contact.js';
import {onRequest as middleware} from '../functions/_middleware.js';

const VALID = 'name=Test+Person&email=test%40example.com&project-type=Not+sure+yet&budget=Under+10k&message=Hello';
const post = (env, {json = true, body = VALID, headers = {}} = {}) => onRequestPost({
  request: new Request('https://example.invalid/api/contact', {
    method: 'POST',
    headers: {'content-type': 'application/x-www-form-urlencoded', ...(json ? {accept: 'application/json'} : {}), ...headers},
    body,
  }),
  env,
});

const store = () => {
  const written = [];
  const kv = new Map();
  return {
    written,
    kv,
    get: async key => kv.get(key) || null,
    put: async (key, value, opts) => { written.push([key, value, opts]); kv.set(key, value); }
  };
};
const failing = message => ({put: async () => { throw new Error(message); }});
// Runs fn with fetch replaced, so webhook calls never leave the process.
const withFetch = async (stub, fn) => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = stub;
  try { return await fn(); } finally { globalThis.fetch = originalFetch; }
};
const HOOK = {NOTIFICATION_WEBHOOK: 'https://webhook.invalid/notify'};
const ENABLED = {ENQUIRY_ENABLED: 'true'};

const cases = [];
const check = (name, fn) => cases.push([name, fn]);

check('a stored enquiry is acknowledged', async () => {
  const ENQUIRY = store();
  const response = await post({...ENABLED, ENQUIRY});
  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), {ok: true});
  assert.equal(ENQUIRY.written.length, 1);
  assert.match(ENQUIRY.written[0][1], /test@example\.com/);
});

check('a page submission is redirected to the receipt only when stored', async () => {
  const response = await post({...ENABLED, ENQUIRY: store()}, {json: false});
  assert.equal(response.status, 303);
  assert.match(response.headers.get('location'), /\/contact\/received\/$/);
});

check('a failed store is an error for the JSON submission', async () => {
  const response = await post({...ENABLED, ENQUIRY: failing('KV unavailable')});
  assert.equal(response.status, 502);
  assert.match((await response.json()).error, /not been received/);
});

check('a failed store is an error for the page submission too', async () => {
  const response = await post({...ENABLED, ENQUIRY: failing('KV unavailable')}, {json: false});
  assert.equal(response.status, 502, 'a no-JavaScript post must not be redirected to the receipt page');
  assert.equal(response.headers.get('location'), null);
});

check('a stored enquiry survives a notification failure', async () => {
  const ENQUIRY = store();
  const response = await withFetch(async () => { throw new Error('network down'); },
    () => post({...ENABLED, ...HOOK, ENQUIRY}));
  assert.equal(response.status, 200);
  assert.equal(ENQUIRY.written.filter(([key]) => key.startsWith('enquiry:')).length, 1);
});

check('notification-only delivery still fails loudly', async () => {
  const response = await withFetch(async () => { throw new Error('network down'); },
    () => post({...ENABLED, ...HOOK}));
  assert.equal(response.status, 502);
});

check('a stored enquiry is also notified', async () => {
  const sent = [];
  await withFetch(async (url, init) => { sent.push(JSON.parse(init.body)); return new Response('ok'); },
    () => post({...ENABLED, ...HOOK, ENQUIRY: store()}));
  assert.equal(sent.length, 1);
  assert.equal(sent[0].enquiry.message, 'Hello');
});

check('an email binding alone does not open intake', async () => {
  // Pages Functions cannot bind send_email; an EMAIL binding is not a delivery path.
  const response = await post({...ENABLED, EMAIL: {send: async () => {}}});
  assert.equal(response.status, 503);
});

check('bindings alone do not open intake', async () => {
  const ENQUIRY = store();
  const response = await post({ENQUIRY});
  assert.equal(response.status, 503);
  assert.equal(ENQUIRY.written.length, 0, 'a deployment that has not enabled intake must store nothing');
});

check('enabled intake without a destination still refuses', async () => {
  assert.equal((await post({...ENABLED})).status, 503);
});

check('the honeypot is accepted and discarded', async () => {
  const ENQUIRY = store();
  const response = await post({...ENABLED, ENQUIRY}, {body: VALID + '&website=spam'});
  assert.equal(response.status, 200);
  assert.equal(ENQUIRY.written.length, 0);
});

check('invalid submissions are rejected before storage', async () => {
  const ENQUIRY = store();
  for (const body of [VALID.replace('message=Hello', 'message='), VALID.replace('test%40example.com', 'not-an-address'),
                      VALID.replace('Test+Person', 'x'.repeat(121))]) {
    assert.equal((await post({...ENABLED, ENQUIRY}, {body})).status, 400, body.slice(0, 40));
  }
  assert.equal(ENQUIRY.written.length, 0);
});

check('stored enquiry sets 90-day expiration TTL', async () => {
  const ENQUIRY = store();
  const response = await post({...ENABLED, ENQUIRY});
  assert.equal(response.status, 200);
  assert.equal(ENQUIRY.written.length, 1);
  const [, , opts] = ENQUIRY.written[0];
  assert.equal(opts?.expirationTtl, 90 * 24 * 60 * 60);
});

check('rate limiting restricts submissions from same IP to 5 per window', async () => {
  const ENQUIRY = store();
  const headers = {'cf-connecting-ip': '203.0.113.42'};
  for (let i = 0; i < 5; i++) {
    const res = await post({...ENABLED, ENQUIRY}, {headers});
    assert.equal(res.status, 200, `request ${i+1} should succeed`);
  }
  const rateLimitedRes = await post({...ENABLED, ENQUIRY}, {headers});
  assert.equal(rateLimitedRes.status, 429);
  assert.match((await rateLimitedRes.json()).error, /Too many enquiries/);
});

check('webhook-only deployment returns 502 when webhook returns HTTP 500', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response('Internal Server Error', {status: 500});
    const response = await post({ENQUIRY_ENABLED: 'true', NOTIFICATION_WEBHOOK: 'https://webhook.invalid/notify'});
    assert.equal(response.status, 502);
    assert.match((await response.json()).error, /Delivery could not be confirmed/);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

check('webhook-only deployment returns 200 when webhook succeeds', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response('{"ok":true}', {status: 200});
    const response = await post({ENQUIRY_ENABLED: 'true', NOTIFICATION_WEBHOOK: 'https://webhook.invalid/notify'});
    assert.equal(response.status, 200);
    assert.equal((await response.json()).ok, true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

check('rate limiting restricts burst submissions from same IP beyond window limit', async () => {
  const ENQUIRY = store();
  const headers = {'cf-connecting-ip': '198.51.100.22'};
  const results = [];
  for (let i = 0; i < 7; i++) {
    results.push(await post({...ENABLED, ENQUIRY}, {headers}));
  }
  const statuses = results.map(r => r.status);
  assert.equal(statuses.slice(0, 5).every(s => s === 200), true);
  assert.equal(statuses.slice(5).every(s => s === 429), true);
});

check('a webhook that times out with no store is refused', async () => {
  const response = await withFetch(async () => { throw new DOMException('timed out', 'TimeoutError'); },
    () => post({...ENABLED, ...HOOK}));
  assert.equal(response.status, 502);
});

check('a stored enquiry is still acknowledged when the webhook fails', async () => {
  const originalFetch = globalThis.fetch;
  try {
    globalThis.fetch = async () => new Response('down', {status: 500});
    const ENQUIRY = store();
    const response = await post({...ENABLED, ENQUIRY, NOTIFICATION_WEBHOOK: 'https://webhook.invalid/notify'});
    assert.equal(response.status, 200);
    assert.equal(ENQUIRY.written.filter(([key]) => key.startsWith('enquiry:')).length, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

check('a no-JavaScript error is a readable page, not JSON', async () => {
  const response = await post({...ENABLED, ENQUIRY: store()}, {json: false, body: 'name=A'});
  assert.equal(response.status, 400);
  assert.match(response.headers.get('content-type'), /text\/html/);
  const page = await response.text();
  assert.match(page, /Missing required field/);
  assert.match(page, /href="\/contact\/"/);
});

check('a post from another website is refused', async () => {
  const ENQUIRY = store();
  const response = await post({...ENABLED, ENQUIRY}, {headers: {origin: 'https://elsewhere.invalid'}});
  assert.equal(response.status, 403);
  assert.equal(ENQUIRY.written.length, 0);
  const same = await post({...ENABLED, ENQUIRY}, {headers: {origin: 'https://example.invalid'}});
  assert.equal(same.status, 200);
});

check('rate limiting never stores the raw IP address', async () => {
  const ENQUIRY = store();
  await post({...ENABLED, ENQUIRY}, {headers: {'cf-connecting-ip': '203.0.113.77'}});
  const keys = ENQUIRY.written.map(([key]) => key);
  assert.ok(keys.some(key => /^ratelimit:[0-9a-f]{32}$/.test(key)), keys.join(', '));
  assert.ok(!keys.join(' ').includes('203.0.113.77'));
});

check('a RATE_LIMIT namespace keeps counters out of the enquiry store', async () => {
  const ENQUIRY = store(), RATE_LIMIT = store();
  await post({...ENABLED, ENQUIRY, RATE_LIMIT}, {headers: {'cf-connecting-ip': '203.0.113.78'}});
  assert.ok(ENQUIRY.written.every(([key]) => key.startsWith('enquiry:')));
  assert.equal(RATE_LIMIT.written.length, 1);
});

check('webhook text cannot ping a whole chat channel', async () => {
  const sent = [];
  const body = 'name=%3C%21channel%3E&email=test%40example.com&project-type=A&budget=B&message=%40here+hello';
  await withFetch(async (url, init) => { sent.push(JSON.parse(init.body)); return new Response('ok'); },
    () => post({...ENABLED, ...HOOK, ENQUIRY: store()}, {body}));
  assert.equal(sent.length, 1);
  assert.ok(!sent[0].text.includes('<!channel>'), sent[0].text);
  assert.ok(!sent[0].text.includes('@here'), sent[0].text);
  assert.equal(sent[0].enquiry.name, '<!channel>', 'the structured copy stays exact');
});

check('middleware hides dotfiles but serves /.well-known/', async () => {
  const visit = path => middleware({request: new Request('https://example.invalid' + path),
    next: async () => new Response('served', {status: 200})});
  assert.equal((await visit('/.factory-build.json')).status, 404);
  assert.equal((await visit('/.env')).status, 404);
  assert.equal((await visit('/.well-known/security.txt')).status, 200);
  assert.equal((await visit('/contact/')).status, 200);
});

let failures = 0;
for (const [name, fn] of cases) {
  try { await fn(); } catch (error) { failures++; console.error(`FAIL: ${name}\n  ${error.message}`); }
}
console.log(failures
  ? `Contact endpoint checks FAILED: ${failures} of ${cases.length}`
  : `Contact endpoint checks passed: ${cases.length} cases, including storage failure, notification failure, webhook errors, unopened intake, and dotfile protection.`);
process.exitCode = failures ? 1 : 0;
