from pathlib import Path
import os


def data_directory() -> Path:
    configured = os.environ.get("LEAVES_DATA_DIR")
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[4] / "data"


def database_path() -> Path:
    return data_directory() / "leaves.sqlite3"
