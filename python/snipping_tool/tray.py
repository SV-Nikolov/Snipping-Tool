import threading
from PIL import Image, ImageDraw
import pystray


def _generate_icon(size=64):
    img = Image.new("RGBA", (size, size), (34, 34, 34, 230))
    d = ImageDraw.Draw(img)
    # Draw a simple scissors-like glyph
    d.line((16, 16, 48, 48), fill=(255, 255, 255, 255), width=4)
    d.line((48, 16, 16, 48), fill=(255, 255, 255, 255), width=4)
    d.ellipse((12, 12, 24, 24), outline=(200, 200, 200, 255), width=3)
    d.ellipse((40, 40, 52, 52), outline=(200, 200, 200, 255), width=3)
    return img


class Tray:
    def __init__(self, on_capture, on_show, on_exit):
        self._on_capture = on_capture
        self._on_show = on_show
        self._on_exit = on_exit
        self._icon = pystray.Icon("Snipping Tool", _generate_icon(), "Snipping Tool")
        self._icon.menu = pystray.Menu(
            pystray.MenuItem("Capture", lambda: self._on_capture()),
            pystray.MenuItem("Show", lambda: self._on_show()),
            pystray.MenuItem("Exit", lambda: self._on_exit()),
        )
        self._thread = None

    def run(self):
        def _run():
            self._icon.run()

        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        try:
            self._icon.stop()
        except Exception:
            pass
