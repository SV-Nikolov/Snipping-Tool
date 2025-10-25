import os
from datetime import datetime
from typing import Optional


def _logs_folder() -> str:
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    return os.path.join(desktop, "Screenshots", "logs")


def log(message: str) -> None:
    try:
        folder = _logs_folder()
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, datetime.now().strftime("%Y-%m-%d") + ".log")
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
    except Exception:
        pass


def log_error(err: BaseException, context: Optional[str] = None) -> None:
    ctx = f" [{context}]" if context else ""
    log(f"ERROR{ctx}: {err}")
