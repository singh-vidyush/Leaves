# Development Setup

## Prerequisites
- macOS for the first desktop build.
- Python 3.11 or newer.
- Node.js 20.19+ or 22.12+ and pnpm.
- Rust and the macOS build tools required by Tauri.

Install current versions from the official [Python](https://www.python.org/downloads/), [Node.js](https://nodejs.org/en/download), [pnpm](https://pnpm.io/installation), and [Tauri prerequisites](https://v2.tauri.app/start/prerequisites/) guides.

## Install Dependencies

From the repository root:

```sh
cd apps/server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
cd ../desktop
pnpm install
```

For a packaged Tauri build, install the backend bundling extra in `apps/server`:

```sh
cd apps/server
python -m pip install -e ".[bundle]"
```

Tauri packages the Python API as a platform-specific sidecar. Build on the same
operating system and architecture as the target; PyInstaller does not
cross-compile the backend.

## Run Leaves

From the repository root, run:

```sh
./scripts/dev.sh
```

This starts the local FastAPI service on `127.0.0.1:8000` and launches the Tauri desktop app. In development, `scripts/dev.sh` owns the API process. Installed Tauri builds start and stop the bundled API sidecar automatically. For browser-only UI work, start the API with `cd apps/server && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log`, then start Vite in another terminal with `cd apps/desktop && pnpm dev`.

During development, the database is written to `data/leaves.sqlite3`; packaged builds use the operating system's Leaves application-data directory. Set `LEAVES_DATA_DIR` to override either location. Credentials use the operating system credential manager (macOS Keychain, Windows Credential Manager, or Linux Secret Service). The API fails closed if no secure store is available.

## Current Scope

The working foundation covers the dashboard, local Markdown folder indexing, full-text search, task extraction, and local scheduling. Google OAuth uses a desktop client ID configured as `GOOGLE_OAUTH_CLIENT_ID`; connect Gmail and Google Calendar from **Connected Context Sources**. Gmail access is read-only and Calendar uses the owned-events scope. When unconnected, both integrations retain sample data for local preview. The app uses a local menu-bar tray; close the window to hide Leaves, and choose **Quit Leaves** from the tray menu to exit.
