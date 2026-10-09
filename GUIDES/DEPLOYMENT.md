# Desktop Deployment Guide

Leaves is packaged as a Tauri desktop app with the FastAPI service bundled as a
platform-specific PyInstaller sidecar. macOS is the first release target. Build
the Python sidecar on the same OS and architecture as the Tauri target.

## Prerequisites

- Python 3.11 or newer, Node.js, pnpm, Rust, and platform-specific Tauri
  prerequisites.
- A virtual environment with the server bundle extra installed:

  ```sh
  cd apps/server
  python3 -m venv .venv
  .venv/bin/python -m pip install -e ".[bundle]"
  ```

## Build

From `apps/desktop`, run:

```sh
pnpm install --frozen-lockfile
pnpm tauri build
```

The Tauri build hooks run `scripts/build_backend.sh` before Rust compilation,
so the configured sidecar exists when Tauri validates its resources. It builds
`apps/server/launcher.py` as a one-file executable in
`apps/desktop/src-tauri/binaries/` with the Rust host target suffix required by
Tauri's `externalBin` configuration. The generated binary is ignored by Git.
Cross-compiling the Python sidecar is intentionally rejected; build on each
target platform.

## Runtime data and credentials

The packaged backend receives Tauri's application-data directory as
`LEAVES_DATA_DIR`. SQLite and indexes stay there. API keys and OAuth
tokens use the operating system's credential manager through Python `keyring`.
The API reports an actionable error when no secure credential backend exists
and does not fall back to plaintext storage. To enable Google connections,
configure a Google Desktop OAuth client ID as `GOOGLE_OAUTH_CLIENT_ID`, register
the loopback callback `http://127.0.0.1:<api-port>/api/auth/google/callback`,
and publish the consent screen as needed for your users. Gmail uses
`gmail.readonly`; Calendar uses `calendar.events.owned`.

Tauri reserves an available loopback port and starts the sidecar there when the
desktop app starts. The frontend gets that port through a Tauri command. Tauri
terminates the sidecar when the app exits. Hiding the window leaves the menu-bar
app and backend alive. Verify a release build on the target platform by checking the
health endpoint, indexing/search, menu-bar hide/restore, and clean process exit.

## Evaluation demo

A hosted or containerized demo is deferred and is not an MVP release gate. It
would need isolated disposable data and must not use real user credentials or
provider accounts. See `SPEC/RELEASE_ACCEPTANCE.md` for release scope.
