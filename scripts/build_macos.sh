#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
SERVER_DIR="$ROOT_DIR/apps/server"
DESKTOP_DIR="$ROOT_DIR/apps/desktop"
TAURI_DIR="$DESKTOP_DIR/src-tauri"
PYTHON_ENV="$SERVER_DIR/.venv"

if [ "$(uname -s)" != "Darwin" ]; then
  echo "Build Leaves.app and Leaves.dmg on macOS; PyInstaller cannot cross-compile the backend." >&2
  exit 1
fi

for tool in python3 node pnpm rustc cargo; do
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing required build tool: $tool" >&2
    exit 1
  fi
done

if ! xcode-select -p >/dev/null 2>&1; then
  echo "Install Xcode Command Line Tools before building Leaves." >&2
  exit 1
fi

if [ ! -x "$PYTHON_ENV/bin/python" ]; then
  python3 -m venv "$PYTHON_ENV"
fi
"$PYTHON_ENV/bin/python" -m pip install --disable-pip-version-check -e "$SERVER_DIR[bundle]"

cd "$DESKTOP_DIR"
pnpm install --frozen-lockfile
pnpm tauri build --bundles app,dmg

echo "Build complete. Generated macOS bundles:"
find "$TAURI_DIR/target/release/bundle" -maxdepth 2 \( -name 'Leaves.app' -o -name '*.dmg' \) -print
