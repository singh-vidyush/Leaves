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

## Run Leaves

From the repository root, run:

```sh
./scripts/dev.sh
```

This starts the local FastAPI service on `127.0.0.1:8000` and launches the Tauri desktop app. For browser-only UI work, start the API with `cd apps/server && .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`, then start Vite in another terminal with `cd apps/desktop && pnpm dev`.

The local database is written to `data/leaves.sqlite3` by default. Set `LEAVES_DATA_DIR` to use a different private local directory.

## Current Scope

The working foundation covers the dashboard, local Markdown folder indexing, and full-text search. Gmail and Google Calendar are shown as planned integrations; provider authorization, scheduling rules, and calendar writes are not implemented yet. The app uses a local menu-bar tray; close the window to hide Leaves, and choose **Quit Leaves** from the tray menu to exit.
