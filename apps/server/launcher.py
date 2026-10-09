"""Entry point used when packaging the local API as a Tauri sidecar."""

import os
import signal
import threading
import time

import uvicorn


def _stop_when_parent_exits(parent_pid: int) -> None:
    """PyInstaller one-file builds can leave their worker alive if killed directly."""
    while True:
        try:
            os.kill(parent_pid, 0)
        except ProcessLookupError:
            os.kill(os.getpid(), signal.SIGTERM)
            return
        except PermissionError:
            pass
        time.sleep(0.5)


def main() -> None:
    port = int(os.environ.get("LEAVES_API_PORT", "8000"))
    parent_pid = os.environ.get("LEAVES_PARENT_PID")
    if parent_pid and parent_pid.isdigit():
        monitor = threading.Thread(
            target=_stop_when_parent_exits,
            args=(int(parent_pid),),
            name="leaves-parent-monitor",
            daemon=True,
        )
        monitor.start()
    # OAuth callback query strings contain short-lived authorization codes.
    uvicorn.run("app.main:app", host="127.0.0.1", port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
