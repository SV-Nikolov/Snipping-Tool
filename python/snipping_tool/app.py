import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import ImageTk
import snipping_tool.core.capture as capture
import snipping_tool.core.storage as storage
import snipping_tool.core.logger as logger
from snipping_tool.tray import Tray


DEFAULT_DELAY_MS = int(os.environ.get("CAPTURE_DELAY_MS", "200"))


class App:
    def __init__(self):
        logger.log("App.__init__: start")
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
        grid_style = {
            "bg": "#007bff",  # blue
            "fg": "white",
            "activebackground": "#0069d9",
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
        self.grid_btn = tk.Button(container, text="Grid", command=self.grid_select, **grid_style)
        self.grid_btn.pack(side=tk.LEFT, padx=4)
        self.exit_btn = tk.Button(container, text="Exit", command=self.exit, **exit_style)
        self.exit_btn.pack(side=tk.LEFT, padx=4)

        # Folder selection menu under the buttons
        self.save_base_dir = None  # None => default Desktop/Screenshots
        # Capture region of interest (ROI): None => full screen; else (left, top, right, bottom) in virtual screen pixels
        self.capture_roi = None

        menu_frame = tk.Frame(self.root, bg="#222222")
        menu_frame.pack(padx=10, pady=(0,10))

        self.folder_menu_btn = tk.Menubutton(
            menu_frame, text="Save folder", bg="#444444", fg="white", relief="raised"
        )
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
        logger.log("App.__init__: window shown")

        # Tray icon
        self.tray = None
        try:
            if os.environ.get("DISABLE_TRAY", "0") not in ("1", "true", "True"): 
                logger.log("App.__init__: creating tray")
                self.tray = Tray(self.capture, self.show, self.exit)
                self.tray.run()
                logger.log("App.__init__: tray started")
            else:
                logger.log("App.__init__: tray disabled by env")
        except Exception as ex:
            logger.log_error(ex, "tray_init")
            self.tray = None

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
            if self.tray:
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

            # Capture
            img = capture.capture_all_monitors_rgb_image()
            # Apply ROI crop if set
            if self.capture_roi:
                l, t, r, b = self.capture_roi
                # Clamp and validate
                l2 = max(0, min(img.width, l))
                t2 = max(0, min(img.height, t))
                r2 = max(0, min(img.width, r))
                b2 = max(0, min(img.height, b))
                if r2 > l2 and b2 > t2:
                    img = img.crop((l2, t2, r2, b2))

            # Save
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
        base_txt = base if base else "Desktop\\Screenshots (default)"
        if not self.capture_roi:
            roi_txt = "full display"
        else:
            l, t, r, b = self.capture_roi
            w = max(0, r - l)
            h = max(0, b - t)
            roi_txt = f"rect {w}x{h} @ ({l},{t})"
        return f"Saving to: {base_txt} | Area: {roi_txt}"

    # Grid selection
    def grid_select(self):
        try:
            # Hide main UI while selecting
            self.root.withdraw()
            self.root.update()
            # Take a snapshot to display for selection
            img = capture.capture_all_monitors_rgb_image()
            sel = self._run_selection_ui(img)
            if sel:
                self.capture_roi = sel  # (left, top, right, bottom)
                l, t, r, b = sel
                logger.log(f"Grid updated to: rect ({l},{t})-({r},{b})")
            else:
                logger.log("Grid not changed (no selection)")
            # Update label
            self.folder_label.config(text=self._folder_label_text())
        except Exception as ex:
            logger.log_error(ex, "grid_select")
        finally:
            self.root.deiconify()
            self.root.update()

    def _run_selection_ui(self, pil_image):
        """Show a fullscreen selection UI over a static screenshot.
        Returns (left, top, right, bottom) in original image pixels, or None if canceled/no selection.
        """
        # Create fullscreen overlay window
        win = tk.Toplevel(self.root)
        win.attributes('-topmost', True)
        win.attributes('-fullscreen', True)
        win.configure(bg='#000000')
        # Canvas to draw
        canvas = tk.Canvas(win, highlightthickness=0, cursor='tcross', bg='#000000')
        canvas.pack(fill=tk.BOTH, expand=True)

        # Fit image to window
        win.update_idletasks()
        ww, wh = win.winfo_width(), win.winfo_height()
        iw, ih = pil_image.width, pil_image.height
        scale = min(ww/iw, wh/ih)
        disp_w, disp_h = max(1, int(iw*scale)), max(1, int(ih*scale))
        off_x, off_y = (ww - disp_w)//2, (wh - disp_h)//2

        disp_img = pil_image.resize((disp_w, disp_h))
        tk_img = ImageTk.PhotoImage(disp_img)
        canvas_img = canvas.create_image(off_x, off_y, image=tk_img, anchor='nw')

        # Selection state
        sel_rect = None
        start = None

        # Dim overlay outside selection
        dim_overlay = canvas.create_rectangle(off_x, off_y, off_x+disp_w, off_y+disp_h, fill='#000000', stipple='gray25')

        def update_overlay_rect(x0, y0, x1, y1):
            nonlocal sel_rect
            # Clamp to image area
            x0c = max(off_x, min(off_x+disp_w, x0))
            y0c = max(off_y, min(off_y+disp_h, y0))
            x1c = max(off_x, min(off_x+disp_w, x1))
            y1c = max(off_y, min(off_y+disp_h, y1))
            if sel_rect is None:
                sel_rect = canvas.create_rectangle(x0c, y0c, x1c, y1c, outline='#00aaff', width=2)
            else:
                canvas.coords(sel_rect, x0c, y0c, x1c, y1c)
            # Update dim to punch a hole: draw four rects or skip for simplicity (keep simple dim)
            return (x0c, y0c, x1c, y1c)

        def on_down(e):
            nonlocal start
            start = (e.x, e.y)

        def on_move(e):
            if start is None:
                return
            update_overlay_rect(start[0], start[1], e.x, e.y)

        selection = {'box': None}

        def on_up(e):
            if start is None:
                return
            x0, y0, x1, y1 = update_overlay_rect(start[0], start[1], e.x, e.y)
            # Convert to original image coordinates
            # Normalize
            if x1 < x0: x0, x1 = x1, x0
            if y1 < y0: y0, y1 = y1, y0
            # Remove offset and scale back
            x0i = int((x0 - off_x) / scale)
            y0i = int((y0 - off_y) / scale)
            x1i = int((x1 - off_x) / scale)
            y1i = int((y1 - off_y) / scale)
            # Clamp to image bounds
            x0i = max(0, min(iw, x0i))
            y0i = max(0, min(ih, y0i))
            x1i = max(0, min(iw, x1i))
            y1i = max(0, min(ih, y1i))
            # Validate rectangle size
            if (x1i - x0i) >= 5 and (y1i - y0i) >= 5:
                selection['box'] = (x0i, y0i, x1i, y1i)
            win.destroy()

        def on_cancel(e=None):
            selection['box'] = None
            win.destroy()

        canvas.bind('<Button-1>', on_down)
        canvas.bind('<B1-Motion>', on_move)
        canvas.bind('<ButtonRelease-1>', on_up)
        win.bind('<Escape>', on_cancel)

        # Block until closed
        win.focus_force()
        win.grab_set()
        win.wait_window()
        return selection['box']


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
