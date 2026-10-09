"""Entry point used when packaging the local API as a Tauri sidecar."""

import os

import uvicorn


def main() -> None:
    port = int(os.environ.get("LEAVES_API_PORT", "8000"))
    # OAuth callback query strings contain short-lived authorization codes.
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
