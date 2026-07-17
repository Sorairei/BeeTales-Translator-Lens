# BeeTales Translator Lens

BeeTales Translator Lens is a privacy-focused Windows desktop application that defines a screen area with a floating lens. It will recognize and translate the text underneath that lens locally, making it useful for conversations in applications such as Discord without manual copy and paste.

## Project status

**Phase 2 — Regional Capture** is implemented.

Available now:

- Transparent, frameless, always-on-top capture lens.
- Movable and resizable capture area.
- Associated floating translation panel with a dark green theme.
- Source languages: Automatic, Spanish, English, Polish, Japanese, and Portuguese.
- Target languages: Spanish, English, Polish, Japanese, and Portuguese.
- Start, force read, pause/resume, copy, lock/unlock, preview, and close controls.
- Real in-memory regional capture through MSS.
- Capture of the lens interior only, excluding its border and controls.
- Support for virtual desktops, multiple monitors, and negative coordinates.
- Native Windows capture exclusion through `SetWindowDisplayAffinity` and `WDA_EXCLUDEFROMCAPTURE`.
- Brief overlay-hiding fallback when native exclusion is unavailable.
- Low-cost image change detection with Low, Normal, and High sensitivity.
- Forced periodic reads so small changes are not missed indefinitely.
- Capture intervals from 250 ms to 2000 ms, plus Manual mode.
- No overlapping jobs: timer ticks are discarded while a capture is running.
- Optional in-app capture preview.
- Automatic, dark-background, light-background, small-text, Japanese, and unprocessed image profiles.
- JSON persistence for geometry, languages, interval, sensitivity, and lens lock state.
- Safe recovery and backup of corrupt settings.
- Initial per-monitor DPI support.

OCR and translation are still simulated. PaddleOCR arrives in Phase 3 and Argos Translate in Phase 4. When a changed frame is captured, the current demonstration displays:

```text
Detected text:
Czy ktoś chce zagrać dzisiaj?

Translation:
¿Alguien quiere jugar hoy?
```

## Requirements

- 64-bit Windows 10 or Windows 11.
- Python 3.11 recommended.
- Administrator privileges are not required.

## Installation and execution

Open PowerShell and run:

```powershell
cd "C:\Users\YOUR_USER\GitHub\BeeTales Translator Lens"

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

python main.py
```

The repository path may contain spaces. Imports and scripts do not assume otherwise.

Alternatively, from the repository root:

```powershell
.\scripts\create_venv.ps1
.\.venv\Scripts\python.exe main.py
```

If PowerShell blocks environment activation, execute `.\.venv\Scripts\python.exe main.py` directly instead of changing the system policy.

## Using Phase 2

1. Drag the small top bar to position the lens above the content you want to capture.
2. Drag the green bottom-right grip to resize it.
3. Choose the source and target languages. They are saved now but are not yet used by a real translation engine.
4. Choose a capture interval, change sensitivity, and image preprocessing profile.
5. Select **Capture preview** if you want to inspect the latest frame in memory.
6. Press **Start**. The app captures the lens interior in a background task.
7. After starting, **Force read** bypasses the change threshold for one cycle.
8. Use **Pause** and **Resume** to stop and restart the timer.
9. Use **Lock lens** to prevent accidental movement and resizing. The panel always remains available to unlock it.
10. Close the app with `×`. Geometry and capture preferences are restored on the next launch.

The preview is never saved to disk. It exists only in application memory.

## Capture pipeline

Phase 2 runs this pipeline:

```text
Calculate the physical lens interior
→ Clip it to the virtual desktop
→ Exclude or briefly hide BeeTales windows
→ Capture through MSS into a NumPy array
→ Build a small grayscale thumbnail
→ Compare changed pixels against the selected threshold
→ Preprocess only changed or forced frames
→ Update the UI on the Qt main thread
```

Only one background capture can be active. If processing takes longer than the selected interval, additional timer events are discarded instead of queued.

## Local data and privacy

Settings are stored through `platformdirs` in a per-user location similar to:

```text
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\config\settings.json
```

Separate directories are reserved for models, cache, logs, history, and debugging. Print the exact location with:

```powershell
python -c "from beetales_translator_lens.storage.paths import data_directory; print(data_directory())"
```

BeeTales Translator Lens has no telemetry and makes no network requests while running. Captures are not written to disk. If `settings.json` is corrupt, it is renamed to `settings.corrupt-DATE.json`, and the application continues with safe defaults.

## Automated tests

Run:

```powershell
python -m pytest
```

The suite covers:

- Settings defaults, validation, persistence, Manual mode, and corrupt-file recovery.
- Paths containing spaces.
- Negative coordinates and virtual-desktop clipping.
- Minimum capture sizes and out-of-bounds regions.
- MSS conversion from BGRA to contiguous BGR memory.
- Monitor enumeration.
- Static frames, large changes, manual force, and periodic forced reads.
- Automatic, unprocessed, and small-text preprocessing behavior.

## Manual Phase 2 test

1. Start the app with `python main.py`.
2. Place the lens over a browser or Discord window and enable **Capture preview**.
3. Press **Start** and confirm that the preview shows only the lens interior.
4. Leave the content static and confirm the status changes to `No changes`.
5. Change the underlying content and confirm that a new frame is accepted.
6. Press **Force read** and confirm that the status reports a forced read.
7. Test Low, Normal, and High sensitivity.
8. Test 250 ms, 750 ms, 2000 ms, and Manual intervals.
9. Pause and verify that no updates occur; resume and verify that one immediate forced read occurs.
10. Move the lens to a secondary monitor, including one positioned to the left of the primary display.
11. Test Windows scaling at 100%, 125%, 150%, or 200% where available.
12. Confirm that the lens and panel do not appear in the capture. On systems where Windows rejects capture exclusion, a very brief opacity fallback may be visible.
13. Restart the application and confirm that geometry, languages, interval, sensitivity, and lock state are restored.

## Repository structure

```text
BeeTales Translator Lens/
├── main.py
├── README.md
├── LICENSE
├── requirements.txt
├── pyproject.toml
├── beetales_translator_lens/
│   ├── application.py
│   ├── constants.py
│   ├── capture/
│   │   ├── capture_engine.py
│   │   ├── change_detector.py
│   │   ├── image_preprocessor.py
│   │   └── screen_region.py
│   ├── platform/
│   │   ├── windows_capture_exclusion.py
│   │   └── windows_dpi.py
│   ├── storage/
│   │   ├── paths.py
│   │   └── settings_store.py
│   ├── ui/
│   │   ├── capture_overlay.py
│   │   ├── main_controller.py
│   │   ├── theme.py
│   │   └── translation_panel.py
│   └── workers/
│       └── capture_worker.py
├── tests/
├── scripts/
└── packaging/
```

The importable package is named `beetales_translator_lens`. The visible product name remains **BeeTales Translator Lens**.

## Roadmap

1. **Phase 1 — Floating interface:** complete.
2. **Phase 2 — Regional capture:** complete.
3. **Phase 3 — OCR:** PaddleOCR, multilingual recognition, confidence, and metrics.
4. **Phase 4 — Translation:** Argos Translate, model management, routes, cache, and language detection.
5. **Phase 5 — Continuous processing:** full pipeline, performance controls, and optional history.
6. **Phase 6 — User experience:** first-run wizard, global shortcuts, system tray, click-through mode, and model management.
7. **Phase 7 — Distribution:** PyInstaller `onedir`, metadata, icon, and portable ZIP.

The included `.spec` file is only a base for Phase 7. Final packaging and PyInstaller are not Phase 2 acceptance requirements.

## License

MIT. See [LICENSE](LICENSE).
