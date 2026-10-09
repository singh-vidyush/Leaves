#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SERVER_DIR="$ROOT_DIR/apps/server"
DESKTOP_DIR="$ROOT_DIR/apps/desktop"

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

(cd "$SERVER_DIR" && "$PYTHON_BIN" -m uvicorn app.main:app --host 127.0.0.1 --port 8000) &
API_PID=$!

cd "$DESKTOP_DIR"
pnpm tauri dev
