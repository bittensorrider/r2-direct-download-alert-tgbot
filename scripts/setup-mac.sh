#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Checking macOS prerequisites"

if ! command -v python3 >/dev/null; then
  echo "Install Python 3.11+ (https://www.python.org/downloads/macos/ or: brew install python@3.12)" >&2
  exit 1
fi

if ! command -v node >/dev/null; then
  echo "Install Node.js LTS (https://nodejs.org/ or: brew install node)" >&2
  exit 1
fi

if ! command -v npm >/dev/null; then
  echo "npm is missing. Reinstall Node.js." >&2
  exit 1
fi

echo "Python: $(python3 --version)"
echo "Node:   $(node --version)"
echo "npm:    $(npm --version)"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env — edit TELEGRAM_* and R2_BUCKETS before continuing."
fi

echo "==> Installing Python dependencies"
make install

echo "==> Installing Worker dependencies"
(
  cd worker
  npm install
)

echo ""
echo "Setup complete."
echo "  1) Edit .env (Telegram + R2_BUCKETS)"
echo "  2) make generate"
echo "  3) ./scripts/setup-cloudflare.sh"
echo "  4) make run (in one terminal)"
echo "  5) make tunnel (in another terminal) OR use a static public URL"
echo "  6) make deploy"
