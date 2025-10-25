from PIL import Image
import mss


def capture_all_monitors_rgb_image():
    """Capture the entire virtual desktop (all monitors) and return a PIL.Image in RGB mode."""
    with mss.mss() as sct:
        monitor = sct.monitors[0]  # 0 = virtual bounding box of all monitors
        raw = sct.grab(monitor)
        # raw.rgb provides bytes in RGB format; size is (width, height)
        img = Image.frombytes("RGB", raw.size, raw.rgb)
        return img
