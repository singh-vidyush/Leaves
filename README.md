# Leaves

Leaves is a local-first desktop app for collecting useful context and organizing
tasks and schedules. The desktop shell is built with Tauri and React; its local
API is built with FastAPI. User data stays on the device, and provider
credentials use the operating system's secure credential store.

## Distribution status

Leaves publishes a macOS installer when a `v*` version tag is pushed. There is
not a released installer yet. After the first successful tagged build, download
the latest installer here:

[Download Leaves for macOS](https://github.com/singh-vidyush/Leaves/releases/latest/download/Leaves-macos.dmg)

[View Leaves releases](https://github.com/singh-vidyush/Leaves/releases)

The release workflow runs the backend tests, builds the app and disk image on a
macOS runner, verifies the bundled Python sidecar, and smoke tests the packaged
backend before publishing the `.dmg`.

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
The build is local and unsigned unless a signing identity is configured. Sharing
the app without Gatekeeper warnings requires Apple Developer ID signing and
notarization.

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
