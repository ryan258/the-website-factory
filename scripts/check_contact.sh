#!/bin/sh
# End-to-end check of the contact Pages Function against a local KV binding.
# Builds a form-enabled site into a temporary directory, serves it with wrangler,
# and exercises the accepted, rejected, and unconfigured paths. Nothing is deployed.
set -eu
root=$(cd "$(dirname "$0")/.." && pwd)
port=${PORT:-8788}
work=$(mktemp -d)
pid=''
# npx starts wrangler, which starts workerd: signal the whole tree, or the old server keeps
# the port and answers for the next configuration under test.
killtree() { # killtree <signal> <pid>
  for child in $(pgrep -P "$2" 2>/dev/null); do killtree "$1" "$child"; done
  kill "-$1" "$2" 2>/dev/null || true
}
trap 'if [ -n "$pid" ]; then killtree TERM "$pid"; fi; rm -rf "$work"' EXIT INT TERM
fail() { echo "FAIL: $1"; tail -20 "$work/dev.log" 2>/dev/null; exit 1; }

HUGO_PARAMS_FORMENABLED=true python3 "$root/scripts/build.py" --destination "$work/site" >/dev/null
grep -q 'action=/api/contact' "$work/site/contact/index.html" || fail 'enabled form does not post to /api/contact'
cp -R "$root/functions" "$work/functions"
cd "$work"

serve() { # serve <extra wrangler args...>
  # A server still listening here would answer for this one and hide its configuration.
  curl -s -o /dev/null "http://127.0.0.1:$port/" && fail "port $port is already in use"
  npx --yes wrangler@4.136.2 pages dev site --port "$port" --compatibility-date 2026-01-01 "$@" >"$work/dev.log" 2>&1 &
  pid=$!
  waited=0
  until curl -sf -o /dev/null "http://127.0.0.1:$port/contact/"; do
    waited=$((waited + 1)); [ "$waited" -gt 60 ] && fail 'wrangler did not start'
    sleep 1
  done
}
stop() {
  killtree TERM "$pid"
  waited=0
  while curl -s -o /dev/null "http://127.0.0.1:$port/"; do
    waited=$((waited + 1))
    if [ "$waited" -gt 20 ]; then killtree KILL "$pid"; fi
    [ "$waited" -gt 30 ] && fail "server on port $port did not stop"
    sleep 1
  done
  wait "$pid" 2>/dev/null || true
  pid=''
}

VALID='name=Test+Person&email=test%40example.com&project-type=Not+sure+yet&budget=Under+10k&message=Hello+there'
# The endpoint allows 5 counted posts per IP per 10 minutes. Each post gets its own client
# address so adding a check never trips that limit by accident; the burst check below
# reuses one address on purpose by setting fixed_ip.
client=0 fixed_ip=''
post() { # post <expected status> <label> <body> [extra curl args...]
  expected=$1 label=$2 body=$3; shift 3
  client=$((client + 1))
  code=$(curl -s -o "$work/body" -w '%{http_code}' -X POST "http://127.0.0.1:$port/api/contact" \
    -H 'Content-Type: application/x-www-form-urlencoded' -H "CF-Connecting-IP: ${fixed_ip:-198.51.100.$client}" --data "$body" "$@")
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
fixed_ip=203.0.113.9
for attempt in 1 2 3 4 5; do
  post 200 "burst $attempt" "$VALID" -H 'Accept: application/json'
done
post 429 'burst over the limit' "$VALID" -H 'Accept: application/json'
fixed_ip=''
stop

serve # No bindings: the endpoint must refuse rather than silently accept.
post 503 'unconfigured endpoint' "$VALID" -H 'Accept: application/json'
stop

# A store alone must not open intake: that is what keeps an inherited binding harmless.
serve --kv ENQUIRY
post 503 'storage without explicit intake' "$VALID" -H 'Accept: application/json'
stop

echo "Contact endpoint checks passed: accepted, stored, redirected, rejected, rate-limited, unconfigured, and not-enabled paths."
echo "Failure paths (storage and notification errors) are covered by scripts/test_contact_endpoint.mjs."
