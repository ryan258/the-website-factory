#!/usr/bin/env sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

MODE="${1:-workshop}"

case "$MODE" in
  site|store|storefront|public)
    PORT=1313
    FLAGS="--serve --port 1313"
    URL="http://127.0.0.1:1313/"
    ;;
  workshop|kit|planner|*)
    PORT=1314
    FLAGS="--workshop --serve --port 1314"
    URL="http://127.0.0.1:1314/site-kit/"
    ;;
esac

# Release port if already bound by a previous server
PIDS=$(lsof -t -i :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  kill $PIDS 2>/dev/null || true
  sleep 0.5
fi

echo "Serving preview at: $URL"
exec python3 scripts/build.py $FLAGS
