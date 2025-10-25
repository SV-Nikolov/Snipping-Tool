import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import snipping_tool.core.capture as capture
import snipping_tool.core.storage as storage
import snipping_tool.core.logger as logger
from snipping_tool.tray import Tray


DEFAULT_DELAY_MS = int(os.environ.get("CAPTURE_DELAY_MS", "200"))


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)  # No window chrome
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#000000")
        self.root.withdraw()  # start hidden until positioned

        # UI
        container = tk.Frame(self.root, bg="#222222", bd=1, highlightthickness=1, highlightbackground="#555555")
        container.pack(padx=10, pady=10)

        capture_style = {
            "bg": "#28a745",  # green
            "fg": "white",
            "activebackground": "#218838",
            "activeforeground": "white",
            "bd": 0,
            "padx": 12,
            "pady": 6,
        }
        exit_style = {
            "bg": "#dc3545",  # red
            "fg": "white",
            "activebackground": "#c82333",
            "activeforeground": "white",
            "bd": 0,
            "padx": 12,
            "pady": 6,
        }
        self.capture_btn = tk.Button(container, text="Capture (Ctrl+Shift+S)", command=self.capture, **capture_style)
        self.capture_btn.pack(side=tk.LEFT, padx=4)
        self.exit_btn = tk.Button(container, text="Exit", command=self.exit, **exit_style)
        self.exit_btn.pack(side=tk.LEFT, padx=4)

        # Folder selection menu under the buttons
        self.save_base_dir = None  # None => default Desktop/Screenshots
        menu_frame = tk.Frame(self.root, bg="#222222")
        menu_frame.pack(padx=10, pady=(0,10))
        self.folder_menu_btn = tk.Menubutton(menu_frame, text="Save folder", bg="#444444", fg="white", relief="raised")
        self.folder_menu = tk.Menu(self.folder_menu_btn, tearoff=0)
        self.folder_menu.add_command(label="Choose folder...", command=self._choose_folder)
        self.folder_menu.add_command(label="Reset to default", command=self._reset_folder)
        self.folder_menu.add_command(label="Open current folder", command=self._open_current_folder)
        self.folder_menu_btn.config(menu=self.folder_menu)
        self.folder_menu_btn.pack(side=tk.LEFT)
        self.folder_label = tk.Label(menu_frame, text=self._folder_label_text(), bg="#222222", fg="#cccccc")
        self.folder_label.pack(side=tk.LEFT, padx=8)

        # Drag-to-move
        container.bind("<Button-1>", self._start_move)
        container.bind("<B1-Motion>", self._do_move)

        # Keyboard shortcut (when focused window)
        self.root.bind_all("<Control-Shift-s>", lambda e: self.capture())

        # Position bottom-right of primary screen, offset by 1 inch
        self.root.update_idletasks()
        # total width/height accounts for both frames
        w = max(container.winfo_reqwidth() + 20, menu_frame.winfo_reqwidth() + 20)
        h = container.winfo_reqheight() + menu_frame.winfo_reqheight() + 20
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        try:
            offset_px = int(self.root.winfo_fpixels("1i"))  # 1 inch in pixels per current DPI
        except Exception:
            offset_px = 96  # reasonable default on Windows
        x = max(0, sw - w - offset_px)
        y = max(0, sh - h - offset_px)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.deiconify()

        # Tray icon
        self.tray = Tray(self.capture, self.show, self.exit)
        self.tray.run()

    def _start_move(self, event):
        self._x = event.x
        self._y = event.y

    def _do_move(self, event):
        x = self.root.winfo_x() + (event.x - self._x)
        y = self.root.winfo_y() + (event.y - self._y)
        self.root.geometry(f"+{x}+{y}")

    def show(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def exit(self):
        try:
            self.tray.stop()
        except Exception:
            pass
        self.root.quit()

    def capture(self):
        try:
            # Hide the UI
            self.root.withdraw()
            self.root.update()

            delay_ms = DEFAULT_DELAY_MS
            try:
                delay_ms = int(os.environ.get("CAPTURE_DELAY_MS", str(DEFAULT_DELAY_MS)))
            except Exception:
                pass
            time.sleep(max(0, delay_ms) / 1000.0)

            # Capture and save
            img = capture.capture_all_monitors_rgb_image()
            path = storage.save_screenshot(img, base_folder=self.save_base_dir)
            if path:
                logger.log(f"Saved screenshot: {path}")
        except Exception as ex:
            logger.log_error(ex, "capture")
        finally:
            # Show the UI again
            self.root.deiconify()
            self.root.update()

    def run(self):
        self.root.mainloop()

    # Folder selection helpers
    def _choose_folder(self):
        path = filedialog.askdirectory(title="Choose screenshots folder")
        if path:
            self.save_base_dir = path
            self.folder_label.config(text=self._folder_label_text())

    def _reset_folder(self):
        self.save_base_dir = None
        self.folder_label.config(text=self._folder_label_text())

    def _open_current_folder(self):
        try:
            base = self.save_base_dir
            if not base:
                # default base folder
                base = os.path.join(os.path.expanduser("~"), "Desktop", "Screenshots")
            os.makedirs(base, exist_ok=True)
            os.startfile(base)
        except Exception as ex:
            logger.log_error(ex, "open_current_folder")

    def _folder_label_text(self) -> str:
        base = self.save_base_dir
        if base:
            return f"Saving to: {base}"
        return "Saving to: Desktop\\Screenshots (default)"


def main():
    logger.log("App.main: starting UI")
    App().run()


if __name__ == "__main__":
    try:
        if sys.stdout:
            try:
                print("Launching Snipping Tool...")
            except Exception:
                pass
        main()
    except Exception as e:
        import traceback
        try:
            traceback.print_exc()
        except Exception:
            pass
        try:
            logger.log_error(e, "startup")
        except Exception:
            pass
        # Keep console window open on error when a TTY is present
        try:
            if sys.stdin and sys.stdin.isatty():
                input("Press Enter to exit...")
        except Exception:
            pass
