#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")/.." && pwd)
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
"$PYTHON_ENV/bin/python" -m pip install --disable-pip-version-check -e "${SERVER_DIR}[bundle]"

cd "$DESKTOP_DIR"
pnpm install --frozen-lockfile
pnpm tauri build --bundles app

BUNDLE_DIR="$TAURI_DIR/target/release/bundle"
APP_PATH=$(find "$BUNDLE_DIR" -maxdepth 3 -type d -name 'Leaves.app' -print -quit)
if [ -z "$APP_PATH" ] || [ ! -d "$APP_PATH" ]; then
  echo "Leaves.app was not found under $BUNDLE_DIR" >&2
  find "$BUNDLE_DIR" -maxdepth 4 -print >&2
  exit 1
fi

APP_VERSION=$(sed -n 's/^[[:space:]]*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$TAURI_DIR/tauri.conf.json" | head -n 1)
if [ -z "$APP_VERSION" ]; then
  echo "Could not read app version from $TAURI_DIR/tauri.conf.json" >&2
  exit 1
fi

DMG_DIR="$BUNDLE_DIR/dmg"
DMG_PATH="$DMG_DIR/Leaves_${APP_VERSION}_$(uname -m).dmg"
STAGING_DIR=$(mktemp -d "${TMPDIR:-/tmp}/leaves-dmg.XXXXXX")
cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

mkdir -p "$DMG_DIR"
ditto "$APP_PATH" "$STAGING_DIR/Leaves.app"
ln -s /Applications "$STAGING_DIR/Applications"
hdiutil create \
  -volname "Leaves" \
  -srcfolder "$STAGING_DIR" \
  -ov \
  -format UDZO \
  "$DMG_PATH"

echo "Build complete. Generated macOS bundles:"
find "$BUNDLE_DIR" -maxdepth 3 \( -name 'Leaves.app' -o -name '*.dmg' \) -print
