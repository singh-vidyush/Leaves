# Tauri Rust Source

`lib.rs` builds the system tray menu and keeps the app available after the window
is closed. `main.rs` starts the Tauri application. The packaged app does not yet
launch a bundled Python backend; development runs FastAPI through `scripts/dev.sh`.
