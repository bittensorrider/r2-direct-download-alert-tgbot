#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Create .env from .env.example first." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

PORT="${WEBHOOK_PORT:-8080}"
PATH_SUFFIX="${WEBHOOK_PATH:-/webhook/event}"
URL="http://127.0.0.1:${PORT}${PATH_SUFFIX}"

payload="$(cat <<EOF
{
  "event_type": "download",
  "bucket": "my-clips",
  "key": "videos/sample.mp4",
  "method": "GET",
  "ip": "203.0.113.10",
  "country": "US",
  "userAgent": "TestClient/1.0",
  "referer": "https://example.com",
  "range": null,
  "bytesSent": 1048576,
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
)"

curl -fsS -X POST "$URL" \
  -H "Authorization: Bearer ${WEBHOOK_SECRET}" \
  -H "Content-Type: application/json" \
  -d "$payload"

echo ""
echo "Webhook test sent to $URL"
