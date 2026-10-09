#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR=$(CDPATH='' cd -- "$(dirname -- "$0")/../.." && pwd)
INSTALLER="$ROOT_DIR/scripts/install.sh"
TEST_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/leaves-installer-test.XXXXXX")
MOCK_BIN="$TEST_ROOT/bin"
mkdir -p "$MOCK_BIN"
trap 'rm -rf "$TEST_ROOT"' EXIT
DMG_CONTENT="Leaves mock DMG fixture"
MOCK_SHA=$(printf '%s' "$DMG_CONTENT" | shasum -a 256 | awk '{print $1}')

cat > "$MOCK_BIN/uname" <<'MOCK'
#!/usr/bin/env bash
case "${1:-}" in
  -s) printf '%s\n' "${MOCK_UNAME_S:-Darwin}" ;;
  -m) printf '%s\n' "${MOCK_UNAME_M:-arm64}" ;;
  *) exec /usr/bin/uname "$@";;
esac
MOCK

cat > "$MOCK_BIN/curl" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
output=""
url="${!#}"
while (($#)); do
  if [[ "$1" == --output ]]; then output="$2"; shift 2; else shift; fi
done
printf '%s\n' "$url" >> "$MOCK_LOG"
if [[ "$url" == *.sha256 ]]; then
  [[ "${MOCK_CHECKSUM_MODE:-valid}" != unavailable ]] || exit 22
  checksum="$MOCK_SHA"
  [[ "${MOCK_CHECKSUM_MODE:-valid}" != invalid ]] || checksum="0000000000000000000000000000000000000000000000000000000000000000"
  checksum_asset="${url##*/}"
  checksum_asset="${checksum_asset%.sha256}"
  printf '%s  %s\n' "$checksum" "$checksum_asset" > "$output"
else
  printf '%s' "$MOCK_DMG_CONTENT" > "$output"
fi
MOCK

cat > "$MOCK_BIN/hdiutil" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$1" == attach ]]; then
  mount_point=""
  while (($#)); do
    if [[ "$1" == -mountpoint ]]; then mount_point="$2"; shift 2; else shift; fi
  done
  if [[ "${MOCK_APP_MODE:-present}" == present ]]; then
    mkdir -p "$mount_point/Leaves.app/Contents"
    printf 'mock-app\n' > "$mount_point/Leaves.app/Contents/mock"
  fi
  printf 'attach\n' >> "$MOCK_LOG"
elif [[ "$1" == detach ]]; then
  printf 'detach\n' >> "$MOCK_LOG"
else
  exit 2
fi
MOCK

cat > "$MOCK_BIN/ditto" <<'MOCK'
#!/usr/bin/env bash
set -euo pipefail
cp -R "$1" "$2"
MOCK

chmod +x "$MOCK_BIN/"*
run_installer() {
  local label="$1" arch="$2" mode="${3:-valid}"
  local case_dir="$TEST_ROOT/$label"
  mkdir -p "$case_dir/tmp" "$case_dir/install"
  MOCK_LOG="$case_dir/log" MOCK_DMG_CONTENT="$DMG_CONTENT" MOCK_SHA="$MOCK_SHA" \
  MOCK_CHECKSUM_MODE="$mode" MOCK_UNAME_M="$arch" LEAVES_INSTALL_DIR="$case_dir/install" \
  MOCK_APP_MODE="${MOCK_APP_MODE:-present}" \
  TMPDIR="$case_dir/tmp" PATH="$MOCK_BIN:$PATH" \
    bash "$INSTALLER" >"$case_dir/stdout" 2>"$case_dir/stderr"
}

run_installer arm64 arm64
grep -q '/Leaves-macos-arm64.dmg$' "$TEST_ROOT/arm64/log"
grep -q '/Leaves-macos-arm64.dmg.sha256$' "$TEST_ROOT/arm64/log"
[[ -f "$TEST_ROOT/arm64/install/Leaves.app/Contents/mock" ]]
grep -q '^detach$' "$TEST_ROOT/arm64/log"
[[ -z "$(find "$TEST_ROOT/arm64/tmp" -mindepth 1 -print -quit)" ]]

run_installer intel x86_64
grep -q '/Leaves-macos-x86_64.dmg$' "$TEST_ROOT/intel/log"
[[ -f "$TEST_ROOT/intel/install/Leaves.app/Contents/mock" ]]

mkdir -p "$TEST_ROOT/reinstall/install/Leaves.app"
printf 'old version\n' > "$TEST_ROOT/reinstall/install/Leaves.app/old"
run_installer reinstall arm64
[[ -f "$TEST_ROOT/reinstall/install/Leaves.app/Contents/mock" ]]
[[ ! -e "$TEST_ROOT/reinstall/install/Leaves.app/old" ]]

if run_installer bad-checksum arm64 invalid; then
  echo "installer accepted a bad checksum" >&2
  exit 1
fi
grep -q 'SHA-256 verification failed' "$TEST_ROOT/bad-checksum/stderr"
[[ ! -e "$TEST_ROOT/bad-checksum/install/Leaves.app" ]]
[[ -z "$(find "$TEST_ROOT/bad-checksum/tmp" -mindepth 1 -print -quit)" ]]

if run_installer missing-checksum arm64 unavailable; then
  echo "installer accepted a missing checksum" >&2
  exit 1
fi
grep -q 'checksum is unavailable' "$TEST_ROOT/missing-checksum/stderr"
[[ -z "$(find "$TEST_ROOT/missing-checksum/tmp" -mindepth 1 -print -quit)" ]]

if MOCK_APP_MODE=missing run_installer missing-app arm64; then
  echo "installer accepted a DMG without Leaves.app" >&2
  exit 1
fi
grep -q '^detach$' "$TEST_ROOT/missing-app/log"
[[ -z "$(find "$TEST_ROOT/missing-app/tmp" -mindepth 1 -print -quit)" ]]

if run_installer unsupported armv7; then
  echo "installer accepted an unsupported architecture" >&2
  exit 1
fi
grep -q 'unsupported Mac architecture' "$TEST_ROOT/unsupported/stderr"

echo "Installer mock tests passed (Apple Silicon, Intel, checksum rejection, update, and cleanup)."
