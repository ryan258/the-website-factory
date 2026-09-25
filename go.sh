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
  workshop|kit|planner)
    PORT=1314
    FLAGS="--workshop --serve --port 1314"
    URL="http://127.0.0.1:1314/site-kit/"
    ;;
  *)
    echo "Error: Unknown preview mode '$MODE'. Expected: site | store | storefront | public | workshop | kit | planner" >&2
    exit 1
    ;;
esac

# Check if port is already bound
PIDS=$(lsof -t -i :"$PORT" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
  echo "Error: Port $PORT is already in use by process (PID: $(echo $PIDS | tr '\n' ' ')). Please stop the running process before starting preview." >&2
  exit 1
fi

echo "Serving preview at: $URL"
exec python3 scripts/build.py $FLAGS
