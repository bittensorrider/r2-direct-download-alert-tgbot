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

if [[ -z "${R2_BUCKETS:-}" ]]; then
  echo "Set R2_BUCKETS in .env (comma-separated bucket names)." >&2
  exit 1
fi

QUEUE_NAME="${R2_QUEUE_NAME:-r2-object-events}"

echo "Generating worker bucket bindings..."
python3 scripts/generate_worker_config.py

echo "Creating queue (ok if it already exists): ${QUEUE_NAME}"
(
  cd worker
  npx wrangler queues create "${QUEUE_NAME}" || true
)

IFS=',' read -ra BUCKETS <<< "${R2_BUCKETS}"
for raw in "${BUCKETS[@]}"; do
  bucket="$(echo "$raw" | xargs)"
  [[ -z "$bucket" ]] && continue

  echo "Configuring event notifications for bucket: ${bucket}"

  (
    cd worker
    npx wrangler r2 bucket notification create "${bucket}" \
      --event-type object-create \
      --queue "${QUEUE_NAME}" || true

    npx wrangler r2 bucket notification create "${bucket}" \
      --event-type object-delete \
      --queue "${QUEUE_NAME}" || true
  )
done

echo ""
echo "Done. Next steps:"
echo "  1) Set WEBHOOK_URL in worker/wrangler.toml"
echo "  2) cd worker && npx wrangler secret put WEBHOOK_SECRET"
echo "  3) make deploy"
