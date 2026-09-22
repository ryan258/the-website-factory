#!/bin/sh
# End-to-end check of the contact Pages Function against a local KV binding.
# Builds a form-enabled site into a temporary directory, serves it with wrangler,
# and exercises the accepted, rejected, and unconfigured paths. Nothing is deployed.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
port=${PORT:-8788}
work=$(mktemp -d)
pid=''
trap 'if [ -n "$pid" ]; then kill "$pid" 2>/dev/null || true; fi; rm -rf "$work"' EXIT INT TERM
fail() { echo "FAIL: $1"; tail -20 "$work/dev.log" 2>/dev/null; exit 1; }

HUGO_PARAMS_FORMENABLED=true python3 "$root/scripts/build.py" --destination "$work/site" >/dev/null
grep -q 'action=/api/contact' "$work/site/contact/index.html" || fail 'enabled form does not post to /api/contact'
cp -R "$root/functions" "$work/functions"
cd "$work"

serve() { # serve <extra wrangler args...>
  npx --yes wrangler@4.136.2 pages dev site --port "$port" --compatibility-date 2026-01-01 "$@" >"$work/dev.log" 2>&1 &
  pid=$!
  waited=0
  until curl -sf -o /dev/null "http://127.0.0.1:$port/contact/"; do
    waited=$((waited + 1)); [ "$waited" -gt 60 ] && fail 'wrangler did not start'
    sleep 1
  done
}
stop() { kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; pid=''; }

VALID='name=Test+Person&email=test%40example.com&project-type=Not+sure+yet&budget=Under+10k&message=Hello+there'
post() { # post <expected status> <label> <body> [extra curl args...]
  expected=$1 label=$2 body=$3; shift 3
  code=$(curl -s -o "$work/body" -w '%{http_code}' -X POST "http://127.0.0.1:$port/api/contact" \
    -H 'Content-Type: application/x-www-form-urlencoded' --data "$body" "$@")
  [ "$code" = "$expected" ] || fail "$label: expected $expected, got $code ($(cat "$work/body"))"
}

serve --kv ENQUIRY --binding ENQUIRY_ENABLED=true
post 200 'valid enquiry'      "$VALID" -H 'Accept: application/json'
grep -q '"ok":true' "$work/body" || fail 'valid enquiry did not return {"ok":true}'
post 303 'no-JavaScript post' "$VALID"
post 200 'honeypot'           "$VALID&website=spam" -H 'Accept: application/json'
post 400 'missing message'    'name=Test&email=test%40example.com&project-type=A&budget=B&message=' -H 'Accept: application/json'
post 400 'invalid email'      "$(echo "$VALID" | sed 's/test%40example.com/not-an-address/')" -H 'Accept: application/json'
post 400 'overlong name'      "name=$(printf 'x%.0s' $(seq 121))&email=test%40example.com&project-type=A&budget=B&message=Hi" -H 'Accept: application/json'
stored=$(grep -rl 'test@example.com' .wrangler/state 2>/dev/null | wc -l)
[ "$stored" -gt 0 ] || fail 'accepted enquiry was not written to KV'
grep -rq 'spam' .wrangler/state 2>/dev/null && fail 'honeypot submission was stored'
stop

serve # No bindings: the endpoint must refuse rather than silently accept.
post 503 'unconfigured endpoint' "$VALID" -H 'Accept: application/json'
stop

# A store alone must not open intake: that is what keeps an inherited binding harmless.
serve --kv ENQUIRY
post 503 'storage without explicit intake' "$VALID" -H 'Accept: application/json'
stop

echo "Contact endpoint checks passed: accepted, stored, redirected, rejected, unconfigured, and not-enabled paths."
echo "Failure paths (storage and notification errors) are covered by scripts/test_contact_endpoint.mjs."
