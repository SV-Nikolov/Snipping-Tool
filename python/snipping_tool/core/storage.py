import os
from datetime import datetime
from typing import Optional
from PIL import Image


def _desktop_path() -> str:
    # Works on Windows for the typical case
    return os.path.join(os.path.expanduser("~"), "Desktop")


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _next_integer_filename(folder: str) -> str:
    i = 1
    while True:
        candidate = os.path.join(folder, f"{i}.png")
        if not os.path.exists(candidate):
            return candidate
        i += 1


def save_screenshot(img: Image.Image, base_folder: Optional[str] = None) -> Optional[str]:
    """Save the given image under base_folder/MM-dd-YYYY/{n}.png and return the file path.

    If base_folder is None, defaults to Desktop/Screenshots.
    """
    try:
        base = base_folder or os.path.join(_desktop_path(), "Screenshots")
        date_folder = datetime.now().strftime("%m-%d-%Y")
        dest_folder = os.path.join(base, date_folder)
        _ensure_dir(dest_folder)

        path = _next_integer_filename(dest_folder)
        img.save(path, format="PNG")
        return path
    except Exception:
        return None
