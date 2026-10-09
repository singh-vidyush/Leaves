#!/bin/sh
set -eu
export PATH="/opt/homebrew/bin:$HOME/.cargo/bin:$PATH"

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SERVER_DIR="$ROOT_DIR/apps/server"
DESKTOP_DIR="$ROOT_DIR/apps/desktop"

# Keep local OAuth configuration out of source control. Explicit environment
# variables take precedence over values in the root .env file.
LEAVES_GOOGLE_CLIENT_ID_FROM_ENV=${GOOGLE_OAUTH_CLIENT_ID:-}
LEAVES_GOOGLE_CLIENT_SECRET_FROM_ENV=${GOOGLE_OAUTH_CLIENT_SECRET:-}
if [ -f "$ROOT_DIR/.env" ]; then
  set -a
  . "$ROOT_DIR/.env"
  set +a
fi
if [ -n "$LEAVES_GOOGLE_CLIENT_ID_FROM_ENV" ]; then
  GOOGLE_OAUTH_CLIENT_ID=$LEAVES_GOOGLE_CLIENT_ID_FROM_ENV
  export GOOGLE_OAUTH_CLIENT_ID
fi
if [ -n "$LEAVES_GOOGLE_CLIENT_SECRET_FROM_ENV" ]; then
  GOOGLE_OAUTH_CLIENT_SECRET=$LEAVES_GOOGLE_CLIENT_SECRET_FROM_ENV
  export GOOGLE_OAUTH_CLIENT_SECRET
fi
unset LEAVES_GOOGLE_CLIENT_ID_FROM_ENV LEAVES_GOOGLE_CLIENT_SECRET_FROM_ENV

if [ -x "$SERVER_DIR/.venv/bin/python" ]; then
  PYTHON_BIN="$SERVER_DIR/.venv/bin/python"
else
  PYTHON_BIN=python3
fi

cleanup() {
  if [ -n "${API_PID:-}" ]; then
    kill "$API_PID" 2>/dev/null || true
    wait "$API_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

(cd "$SERVER_DIR" && "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log) &
API_PID=$!

cd "$DESKTOP_DIR"
pnpm tauri dev
