/* Failure-path checks for the contact Pages Function, with no network or Cloudflare account.
   The endpoint is called directly with stub bindings; check_contact.sh covers the real ones. */
import assert from 'node:assert/strict';
import {onRequestPost} from '../functions/api/contact.js';

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
const mailer = () => {
  const sent = [];
  return {sent, send: async message => { sent.push(message); }};
};
const failingMailer = () => ({send: async () => { throw new Error('mailbox unavailable'); }});
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
  const response = await post({...ENABLED, ENQUIRY, EMAIL: failingMailer(), ENQUIRY_TO: 'a@b.invalid', ENQUIRY_FROM: 'c@d.invalid'});
  assert.equal(response.status, 200);
  assert.equal(ENQUIRY.written.length, 1);
});

check('notification-only delivery still fails loudly', async () => {
  const response = await post({...ENABLED, EMAIL: failingMailer(), ENQUIRY_TO: 'a@b.invalid', ENQUIRY_FROM: 'c@d.invalid'});
  assert.equal(response.status, 502);
});

check('a stored enquiry is also notified', async () => {
  const EMAIL = mailer();
  await post({...ENABLED, ENQUIRY: store(), EMAIL, ENQUIRY_TO: 'a@b.invalid', ENQUIRY_FROM: 'c@d.invalid'});
  assert.equal(EMAIL.sent.length, 1);
  assert.match(EMAIL.sent[0].text, /message: Hello/);
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

let failures = 0;
for (const [name, fn] of cases) {
  try { await fn(); } catch (error) { failures++; console.error(`FAIL: ${name}\n  ${error.message}`); }
}
console.log(failures
  ? `Contact endpoint checks FAILED: ${failures} of ${cases.length}`
  : `Contact endpoint checks passed: ${cases.length} cases, including storage failure, notification failure, and unopened intake.`);
process.exitCode = failures ? 1 : 0;
