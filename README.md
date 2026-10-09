# Leaves

Leaves is a local-first desktop app for collecting useful context and organizing
tasks and schedules. The desktop shell is built with Tauri and React; its local
API is built with FastAPI. User data stays on the device, and provider
credentials use the operating system's secure credential store.

## Install Leaves on macOS

Leaves is free to install. The app is currently unsigned, so macOS may show a
Gatekeeper warning the first time it opens. The installer needs only the
macOS-provided `curl`, `bash`, `hdiutil`, `ditto`, and `shasum` tools; it does
not need Python, Node.js, Rust, Homebrew, or `sudo` for a normal installation.

Run this command in Terminal:

```sh
curl -fsSL https://raw.githubusercontent.com/singh-vidyush/Leaves/main/scripts/install.sh | bash
```

The installer detects Apple Silicon or Intel, downloads the matching DMG from
the latest GitHub Release, verifies its published SHA-256 checksum, and replaces
an existing Leaves.app. It installs to `/Applications` when writable, or to
`~/Applications` if macOS permissions prevent that. After installation, open
Leaves from Finder or run the `open -a` command printed by the installer.

If Gatekeeper blocks the unsigned app:

1. Attempt to open Leaves from Applications.
2. Open **System Settings → Privacy & Security**.
3. Select **Open Anyway** for Leaves if it is available.
4. Confirm that you want to open the app.

You can also download Leaves directly from [GitHub Releases](https://github.com/singh-vidyush/Leaves/releases/latest).
The current `v0.1.0` release has a legacy [DMG download](https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos.dmg)
without a published checksum, so the curl installer intentionally refuses it.
The architecture-specific DMG and checksum links are available after a new
release is published: [Apple Silicon DMG](https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos-arm64.dmg) ·
[Intel DMG](https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos-x86_64.dmg).

To update or reinstall Leaves, run the same curl command again. It verifies
the new download before replacing the app; your existing app data is kept.

The release workflow builds separate Apple Silicon and Intel installers and
publishes a SHA-256 checksum with each DMG when a version tag is pushed.

## Requirements

- macOS for the desktop app build
- Python 3.11 or newer
- Node.js 20.19+ or 22.12+, with pnpm
- Rust and Xcode Command Line Tools
- The platform prerequisites listed in the [Tauri setup guide](https://v2.tauri.app/start/prerequisites/)

Install Python from [python.org](https://www.python.org/downloads/), Node.js
from [nodejs.org](https://nodejs.org/en/download), pnpm from
[pnpm.io](https://pnpm.io/installation), and Rust from
[rustup.rs](https://rustup.rs/).

## Install and run

From Terminal:

```sh
git clone https://github.com/singh-vidyush/Leaves.git
cd Leaves
python3 -m venv apps/server/.venv
apps/server/.venv/bin/python -m pip install -e "apps/server[bundle]"
cd apps/desktop
pnpm install --frozen-lockfile
cd ../..
./scripts/dev.sh
```

The development script starts the local API and launches the Tauri desktop app.
Connect Google and save OAuth Client ID and Client Secret in Leaves Settings;
no `.env` file is needed. OAuth values and tokens are stored in the operating
system credential store. The backend listens only on the local machine.

## Build the macOS app and installer

On a Mac with Python 3.11+, Node.js, pnpm, Rust, and Xcode Command Line Tools,
run one command from the repository root:

```sh
./scripts/build_macos.sh
```

This creates `Leaves.app` and a `.dmg` under
`apps/desktop/src-tauri/target/release/bundle/`. The Python backend is bundled
as a Tauri sidecar and starts automatically. User data is stored persistently
in the macOS application data directory. Build on the Mac architecture you
intend to use; PyInstaller does not cross-compile the sidecar.
The local build is unsigned and may show a Gatekeeper warning on first launch.

To publish a new version, update the version in `apps/desktop/package.json`,
`apps/desktop/src-tauri/tauri.conf.json`,
`apps/desktop/src-tauri/Cargo.toml`, and `apps/server/pyproject.toml` to the same
value. Commit and push those changes, then create and push the matching tag (for
example, `v1.2.3`):

```sh
git tag v1.2.3
git push origin v1.2.3
```

The macOS Release workflow validates the matching versions and publishes
`Leaves-macos.dmg` to that GitHub Release after all checks pass.

## Google integrations

Enter the Client ID and Client Secret from the same Google OAuth Desktop client
in Leaves Settings. Leaves stores them and OAuth tokens in the operating
system's secure credential store, not in SQLite, browser storage, or Git. The
app uses PKCE, requests read-only Gmail access, and requests access to events
owned by the user.
