## Copilot / AI agent instructions for SV-Nikolov/Snipping-Tool (Python)

Purpose: give an AI agent the minimal, project-specific context to be productive here. Keep risky changes small, preserve capture behavior, and use the provided run script.

1) Big picture
 - Windows desktop utility implemented in Python (Tkinter) that captures the entire virtual desktop across all monitors.
 - Minimal always-on-top floating UI with Capture and Exit; tray menu offers Capture/Show/Exit.
 - Storage: `%UserProfile%\Desktop\Screenshots\MM-dd-YYYY\{n}.png` using the next available integer.

2) Key files (open these first)
 - Entry/UI: `python/snipping_tool/app.py` (App class; hide-delay-capture-show; tray; shortcut).
 - Capture: `python/snipping_tool/core/capture.py` (mss over virtual desktop returns PIL Image).
 - Storage: `python/snipping_tool/core/storage.py` (folder structure + sequential numbering).
 - Logging: `python/snipping_tool/core/logger.py` (daily log files under Desktop/Screenshots/logs).
 - Tray: `python/snipping_tool/tray.py` (pystray icon + menu callbacks).
 - Runner: `python/run.ps1` (creates venv, installs deps, runs the app).

3) Run / debug
 - PowerShell on Windows:
```powershell
cd c:\Source\Snipping-Tool\python
.\run.ps1
```
 - Configurable delay (ms) via env var `CAPTURE_DELAY_MS`.

4) Behaviors to preserve (contract)
 - Hide UI → short delay (~200ms default) → capture full virtual desktop → save → show UI.
 - File layout and naming must remain: Desktop/Screenshots/MM-dd-YYYY/{n}.png with next-available number.
 - Tray menu includes Capture/Show/Exit; Ctrl+Shift+S triggers capture when window is focused.

5) Safe-edit rules
 - Capture is high-risk (multi-monitor/DPI). Keep diffs small; manually verify after changes.
 - Make tunables (like delay) configurable with conservative defaults; update README when changed.
 - Avoid heavy dependencies; justify any new package.

6) Useful repo queries
 - `capture_all_monitors_rgb_image`, `save_screenshot`, `CAPTURE_DELAY_MS`, `pystray`, `mss`, `Pillow`.

7) PR & commit guidance
 - Small PRs with a 1-line summary + 2–4 line rationale; include manual test notes (what you clicked, saved path).
 - If changing storage/naming, include before/after examples and edge cases (existing files, empty folder).

8) When blocked
 - If run fails, capture Python version and pip package versions; re-run via `python/run.ps1` to recreate the env and include the exact error.
## Copilot / AI agent instructions for SV-Nikolov/Snipping-Tool

Purpose: give an AI coding agent the minimal, high-value context to be productive in THIS repository. Follow these concrete patterns and keep risky changes small.

1) Big picture (from README.md)
 - App types: Windows desktop utility with two implementations
	 - .NET Framework WPF (classic) in `SnippingTool/`
	 - Python Tkinter in `python/snipping_tool/`
 - Both provide a tiny always-on-top UI with Capture and Exit and save full virtual-desktop screenshots across all monitors.
 - Architecture: 3 layers
	 - UI: `MainWindow.xaml` (+ `.xaml.cs`) handles button clicks and visibility.
	 - Core: static managers `ScreenshotManager` and `StorageManager` orchestrate capture and saving.
	 - System APIs: `System.Windows.Forms.SystemInformation.VirtualScreen` for multi-monitor bounds; `System.Drawing`/`Graphics.CopyFromScreen` for capture; `System.IO` for saving.
 - Storage rules: `%UserProfile%\Desktop\Screenshots\MM-dd-yyyy\{n}.png` where n is the next integer not yet used.

2) Key files and symbols (search first)
 - UI events: `CaptureButton_Click`, `ExitButton_Click` in `MainWindow.xaml.cs`.
 - Capture flow: `MainWindow.PerformCaptureAsync()` → `ScreenshotManager.TakeScreenshot()` → `StorageManager.SaveScreenshot(Bitmap)`.
 - System tray: `Core.TrayIconManager` (Capture/Show/Exit via NotifyIcon).
 - Logging: `Core.Logger` writes to Desktop/Screenshots/logs.
 - Config: `App.config` appSetting `CaptureDelayMs` (read via `ConfigurationManager`).
 - Important APIs: `SystemInformation.VirtualScreen`, `Graphics.CopyFromScreen`, `ImageFormat.Png`, DPI settings in `app.manifest`.
 - Python equivalents:
	 - Entry: `python/snipping_tool/app.py` (`App` class with `capture`, tray via `pystray`)
	 - Capture: `python/snipping_tool/core/capture.py` (mss over all monitors)
	 - Storage: `python/snipping_tool/core/storage.py`
	 - Logging: `python/snipping_tool/core/logger.py`
	 - Run script: `python/run.ps1`

3) Build / run / debug
 - .NET (classic .NET Framework)
 - Use Visual Studio on Windows:
	 - Open `Snipping-Tool.sln`, set project `SnippingTool` as Startup Project, press F5 to debug.
 - Command line build with MSBuild (paths vary by VS version):
	 - Example (PowerShell):
```powershell
# Update the MSBuild path if needed
msbuild "c:\Source\Snipping-Tool\Snipping-Tool.sln" /t:Build /p:Configuration=Debug
```
 - Project references for classic WPF:
	 - Ensure references to System.Windows.Forms and System.Drawing (not System.Drawing.Common).
	 - If you later migrate to SDK-style .NET, switch to System.Drawing.Common.
 - Python
	 - Install and run via `python/run.ps1` (creates venv, installs `mss`, `Pillow`, `pystray`, then runs `snipping_tool.app`).
	 - Configurable delay via env var `CAPTURE_DELAY_MS`.

4) Required behaviors to preserve
 - Hide UI before capture, then show it after: set `this.Visibility = Hidden`, delay ~200ms, capture, then restore to `Visible`.
 - Capture ALL monitors using the virtual screen bounds; do not switch to per-monitor screenshots unless explicitly requested.
 - Save path/date format and sequential numbering must remain exact: `MM-dd-yyyy` and `1.png, 2.png, ...` skipping existing numbers.
 - Tray icon must offer Capture/Show/Exit actions; keyboard shortcut Ctrl+Shift+S should trigger capture when window focused.

5) Safe-edit rules (risky areas)
 - Capture logic (CopyFromScreen, DPI, multi-monitor) is high-risk. Keep diffs small and test on multi-monitor if possible.
 - If you change the delay before capture, prefer making it configurable with a default of 200ms; document rationale in the PR.
 - Windows-only dependencies: maintain Windows targeting in project settings and any preprocessor guards (e.g., "# if WINDOWS" / "# endif").
	- If you edit DPI behavior, update `app.manifest` and confirm per-monitor behavior manually.

6) Adding features (patterns)
 - Put new orchestration in Core (e.g., add `RegionCaptureManager`), keep UI handlers thin (call into Core, minimal logic).
 - For storage changes (e.g., different filename scheme), implement in `StorageManager` and update the sequential-number logic with unit tests.

7) Quick repo queries to run before coding
 - Find entry and UI: search for `MainWindow.xaml` and `CaptureButton_Click`.
 - Find capture: search for `ScreenshotManager` and `CopyFromScreen`.
 - Find storage: search for `StorageManager`, `ImageFormat.Png`, and `Screenshots` path logic.

8) Local verification checklist (manual, since OS capture is hard to unit-test)
 - Start app: a small always-on-top window appears with Capture and Exit.
 - Click Capture: window hides, then reappears ~200ms later; a PNG appears under Desktop\Screenshots\<today> with the next integer name and without the UI in the image.
 - Multi-monitor: resulting image spans all monitors (virtual desktop bounds).

9) PR & commit conventions
 - Keep behavior-changing PRs under ~200 LOC; include a short rationale and manual test notes (what you clicked, where the file was saved).
 - If adding packages or changing target frameworks, note the exact `TargetFramework` and why.

10) Gaps to confirm
 - Exact target framework and SDK: check the `.csproj`. If classic .NET Framework, prefer Visual Studio build instructions in the PR.
 - If CI exists in `.github/workflows`, mirror its SDK versions locally when reproducing.
