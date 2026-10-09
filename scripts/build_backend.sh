#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SERVER_DIR="$ROOT_DIR/apps/server"
TAURI_DIR="$ROOT_DIR/apps/desktop/src-tauri"
BIN_DIR="$TAURI_DIR/binaries"

if [ ! -x "$SERVER_DIR/.venv/bin/python" ]; then
  echo "Missing $SERVER_DIR/.venv/bin/python; install the server bundle extra first." >&2
  exit 1
fi
if ! "$SERVER_DIR/.venv/bin/python" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller is missing; install apps/server with the [bundle] extra." >&2
  exit 1
fi

if ! command -v rustc >/dev/null 2>&1; then
  echo "Rust is required to determine the Tauri sidecar target triple." >&2
  exit 1
fi
HOST_TRIPLE=$(rustc -vV | sed -n 's/^host: //p')
if [ -z "$HOST_TRIPLE" ]; then
  echo "Could not determine the Rust host target triple." >&2
  exit 1
fi
TARGET_TRIPLE=${TAURI_ENV_TARGET_TRIPLE:-$HOST_TRIPLE}
if [ "$TARGET_TRIPLE" != "$HOST_TRIPLE" ]; then
  echo "The Python backend sidecar must be built on its target platform ($TARGET_TRIPLE; host is $HOST_TRIPLE)." >&2
  exit 1
fi

mkdir -p "$BIN_DIR"
rm -f "$BIN_DIR/leaves-api-$TARGET_TRIPLE"
cd "$SERVER_DIR"
"$SERVER_DIR/.venv/bin/python" -m PyInstaller \
    --clean --noconfirm --onefile \
    --name "leaves-api-$TARGET_TRIPLE" \
    --distpath "$BIN_DIR" \
    --workpath "${TMPDIR:-/tmp}/leaves-pyinstaller-work" \
    --specpath "${TMPDIR:-/tmp}/leaves-pyinstaller-spec" \
    --hidden-import app.main \
    --collect-submodules app \
    --collect-all keyring \
    launcher.py

test -x "$BIN_DIR/leaves-api-$TARGET_TRIPLE"
