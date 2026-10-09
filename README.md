# Leaves

Leaves is a local-first desktop app for collecting useful context and organizing
tasks and schedules. The desktop shell is built with Tauri and React; its local
API is built with FastAPI. User data stays on the device, and provider
credentials use the operating system's secure credential store.

## Distribution status

This repository contains source code only. It does not currently publish a
prebuilt installer or app download. You can build and run Leaves locally by
following the steps below.

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
The first run builds the Python backend sidecar for the current operating
system and architecture. The backend listens only on the local machine.

## Build a local app

After installing the dependencies above, build the desktop app on the same
operating system and architecture where it will run:

```sh
cd apps/desktop
pnpm tauri build
```

The generated installer is local to your machine; this repository does not
upload or publish it. PyInstaller does not cross-compile the backend sidecar.

## Google integrations

To connect Gmail and Google Calendar, configure a Google Desktop OAuth client
ID as `GOOGLE_OAUTH_CLIENT_ID` and set up the corresponding loopback callback.
The app requests read-only Gmail access and access to events owned by the user.
