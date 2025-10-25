Application Architecture: Windows Screenshot Utility

1. Application Overview

A lightweight, "always-on" desktop utility for Windows 11 designed for quick, unobtrusive screen captures. The application presents a minimal UI with two buttons ("Capture" and "Exit") that floats on top of other windows. On capture, the UI vanishes, a full-screen screenshot is taken, and the UI reappears. Screenshots are saved in a structured, date-based folder system on the user's Desktop.

2. Core Requirements

Functional Requirements

FR1: The application must display a small, floating window with two buttons: "Capture" and "Exit".

FR2: This window must always be on top of other applications.

FR3: Pressing "Capture" must:

Instantly hide the UI.

Capture the entire screen contents (including all monitors).

Re-display the UI.

FR4: Pressing "Exit" must terminate the application.

FR5: Screenshots must be saved to a base folder: %UserProfile%\Desktop\Screenshots.

FR6: Inside the base folder, screenshots must be stored in sub-folders named by date, using the format MM-dd-yyyy (e.g., 10-25-2025).

FR7: Screenshot files within a date folder must be named with a sequential integer ID (e.g., 1.png, 2.png, 3.png).

Non-Functional Requirements

NFR1: The application must be fast and responsive, with minimal delay during capture.

NFR2: The application must work entirely offline.

NFR3: The UI itself must not be included in the screenshot.

NFR4: The application should be resource-efficient (low CPU/RAM).

3. Architecture (Python)

We use a simple, 3-tier structure for this desktop application.

UI Layer (Presentation): A minimal Tkinter window responsible for displaying the buttons and capturing user input.

Core Logic (Service Layer): Functions that orchestrate the flow (hiding UI, triggering capture, saving, logging).

Data/API Layer (System Integration): `mss` for screen capture across monitors, Pillow for image handling, and `os`/`pathlib` for file operations.

Component Flow (Capture Event)

User clicks "Capture" (or presses Ctrl+Shift+S while focused) in the UI.

UI hides the window, waits a brief delay (default 200 ms) so it won’t appear in the capture.

UI calls `capture.capture_all_monitors_rgb_image()` to get a PIL Image.

Storage saves the image via `storage.save_screenshot(img)` into Desktop\Screenshots\MM-dd-YYYY\{n}.png.

UI shows the window again.

4. Technology Stack (Python)

Platform: Python 3.x (Windows 11)

Libraries:

- `mss` (multi-monitor screen capture)
- `Pillow` (image saving)
- `pystray` (system tray icon)
- `tkinter` (built-in UI)

5. Detailed Components

UI: `python/snipping_tool/app.py` — Tkinter always-on-top, borderless window; Capture/Exit buttons; drag-to-move; Ctrl+Shift+S shortcut; tray icon with Capture/Show/Exit.

Capture: `python/snipping_tool/core/capture.py` — uses mss to capture the virtual desktop (all monitors) and returns a PIL Image.

Storage: `python/snipping_tool/core/storage.py` — saves to `%UserProfile%\Desktop\Screenshots\MM-dd-YYYY\{n}.png` using next-available integer naming.

Logging: `python/snipping_tool/core/logger.py` — writes logs to `%UserProfile%\Desktop\Screenshots\logs\yyyy-MM-dd.log`.

6. Key Considerations & Risks

Permissions: Needs write access to the Desktop. Controlled-folder access could block writes.

Multi-Monitor & DPI: `mss` captures the virtual desktop. DPI differences between monitors can influence coordinates on some setups; multi-monitor coverage is handled by using the virtual bounds.

Fullscreen Apps: Exclusive fullscreen content may not capture reliably (common to all desktop capture methods).

7. Build and Run (Python)

PowerShell on Windows:

```powershell
cd c:\Source\Snipping-Tool\python
.\run.ps1
```

Optional: configurable delay before capture (milliseconds):

```powershell
$env:CAPTURE_DELAY_MS = 200
cd c:\Source\Snipping-Tool\python
.\run.ps1
```

8. Usage Tips and Quality-of-Life

- Tray icon with Capture / Show / Exit
- Keyboard shortcut: Ctrl+Shift+S while window focused
- Drag to move the floating window
- Logs written to `%UserProfile%\Desktop\Screenshots\logs\yyyy-MM-dd.log`

9. DPI and Multi-Monitor

- Capture uses `mss` on the virtual desktop (all monitors)

10. Run without installing tools (standalone EXE)

If you don't want to install Python locally, use the prebuilt executable produced by GitHub Actions:

- On any push/PR, the workflow "Build Windows EXE (Python)" runs and uploads an artifact named `SnippingToolPy-windows`.
- Download the artifact from the Actions tab and run `SnippingToolPy.exe` directly.

Build locally (optional):

```powershell
cd c:\Source\Snipping-Tool\python
.\build.ps1
```

This produces `dist\SnippingToolPy.exe` which you can copy to another Windows machine and run without installing Python.