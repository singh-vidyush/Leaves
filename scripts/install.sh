#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY="singh-vidyush/Leaves"
DOWNLOAD_ROOT="https://github.com/${REPOSITORY}/releases/latest/download"

fail() {
  printf 'Leaves installer: %s\n' "$*" >&2
  exit 1
}

if [[ "$(uname -s)" != "Darwin" ]]; then
  fail "this installer supports macOS only. Download a release from https://github.com/${REPOSITORY}/releases"
fi

case "$(uname -m)" in
  arm64|aarch64) asset_arch="arm64" ;;
  x86_64) asset_arch="x86_64" ;;
  *) fail "unsupported Mac architecture: $(uname -m)" ;;
esac

asset_name="Leaves-macos-${asset_arch}.dmg"
work_dir=$(mktemp -d "${TMPDIR:-/tmp}/leaves-install.XXXXXX") || fail "could not create a temporary directory"
mount_point="$work_dir/mount"
mounted=0
install_dir=""
install_path=""
staging_path=""
backup_path=""

cleanup() {
  result=$?
  if [[ "$mounted" -eq 1 ]]; then
    hdiutil detach "$mount_point" -quiet >/dev/null 2>&1 || true
  fi
  if [[ -n "$backup_path" && -e "$backup_path" && -n "$install_path" && ! -e "$install_path" ]]; then
    mv "$backup_path" "$install_path" 2>/dev/null || true
  fi
  if [[ -n "$staging_path" && -e "$staging_path" ]]; then
    rm -rf "$staging_path"
  fi
  if [[ -n "$backup_path" && -e "$backup_path" ]]; then
    rm -rf "$backup_path"
  fi
  rm -rf "$work_dir"
  exit "$result"
}
trap cleanup EXIT
mkdir -p "$mount_point" || fail "could not prepare a temporary mount point"

dmg_path="$work_dir/$asset_name"
checksum_path="$work_dir/$asset_name.sha256"

printf 'Downloading Leaves for %s...\n' "$asset_arch"
curl --fail --location --silent --show-error --retry 3 --connect-timeout 15 \
  --output "$dmg_path" "$DOWNLOAD_ROOT/$asset_name" \
  || fail "could not download $asset_name from the latest GitHub Release"
curl --fail --location --silent --show-error --retry 3 --connect-timeout 15 \
  --output "$checksum_path" "$DOWNLOAD_ROOT/$asset_name.sha256" \
  || fail "the release checksum is unavailable; refusing to install an unverified download"

read -r expected_checksum checksum_asset < "$checksum_path" \
  || fail "the release checksum file is empty"
if [[ ! "$expected_checksum" =~ ^[[:xdigit:]]{64}$ || "$checksum_asset" != "$asset_name" ]]; then
  fail "the release checksum file has an invalid format"
fi
if ! (cd "$work_dir" && printf '%s  %s\n' "$expected_checksum" "$asset_name" | shasum --check --algorithm 256 --status); then
  fail "SHA-256 verification failed for the downloaded DMG"
fi
printf 'Checksum verified.\n'

mounted=1
hdiutil attach -readonly -nobrowse -mountpoint "$mount_point" "$dmg_path" >/dev/null \
  || fail "could not mount the downloaded disk image"
app_source="$mount_point/Leaves.app"
if [[ ! -d "$app_source" ]]; then
  fail "Leaves.app was not found in the downloaded disk image"
fi

if [[ -n "${LEAVES_INSTALL_DIR:-}" ]]; then
  install_dir="$LEAVES_INSTALL_DIR"
  mkdir -p "$install_dir" || fail "cannot create installation directory $install_dir"
elif [[ -d "/Applications" && -w "/Applications" ]]; then
  install_dir="/Applications"
else
  install_dir="$HOME/Applications"
  mkdir -p "$install_dir" || fail "cannot write to /Applications or create $install_dir"
  printf 'No write access to /Applications; installing for this user in %s instead.\n' "$install_dir"
fi

install_path="$install_dir/Leaves.app"
staging_path="$install_dir/.Leaves.app.new.$$"
backup_path="$install_dir/.Leaves.app.backup.$$"
ditto "$app_source" "$staging_path" || fail "could not copy Leaves.app to $install_dir"

if [[ -e "$install_path" ]]; then
  mv "$install_path" "$backup_path" || fail "could not move the existing Leaves.app aside"
fi
if ! mv "$staging_path" "$install_path"; then
  if [[ -e "$backup_path" ]]; then
    mv "$backup_path" "$install_path" || true
  fi
  fail "could not install Leaves.app to $install_dir"
fi
staging_path=""
if [[ -e "$backup_path" ]]; then
  rm -rf "$backup_path" || fail "Leaves was installed, but the old app could not be removed at $backup_path"
  backup_path=""
fi

printf '\nLeaves is installed at %s\n' "$install_path"
printf 'Launch it from Finder, or run: open -a "%s"\n' "$install_path"
printf 'If macOS blocks the unsigned app, follow the Gatekeeper instructions in the Leaves README.\n'
