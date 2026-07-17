# BeeTales Translator Lens

BeeTales Translator Lens is a privacy-focused Windows desktop application that recognizes and translates text underneath a floating screen lens. Capture, OCR, language detection, and translation run locally after the required models have been downloaded.

## Project status

**Phase 7 — Distribution** is implemented.

Version 0.6.1 fixes packaged startup logging and makes every language, capture, settings, wizard, and model-management drop-down DPI-safe. Compact panel layouts now scroll instead of compressing or overlapping controls.

Available now:

- Transparent, frameless, always-on-top capture lens that can be moved, resized, and locked.
- Floating translation panel with source and target language selectors.
- English-only interface and status messages.
- Source languages: Automatic, Spanish, English, Polish, Japanese, and Portuguese.
- Target languages: Spanish, English, Polish, Japanese, and Portuguese.
- Real regional screen capture across multiple monitors and negative desktop coordinates.
- Capture exclusion for the BeeTales windows, with an opacity fallback when Windows rejects native exclusion.
- Low-cost image change detection, periodic forced reads, selectable intervals, and Manual mode.
- Local PaddleOCR 3.x recognition with reusable per-language pipelines.
- Local Lingua language detection restricted to the five supported languages.
- Local Argos Translate translation with direct routes or an English pivot.
- On-demand translation-model discovery, download, and installation after confirmation.
- Bounded in-memory LRU translation cache, with optional versioned persistence.
- Optional bounded translation history, disabled by default and deduplicated.
- OCR text normalization that retains Unicode, line breaks, and likely chat username prefixes.
- Background capture, OCR, detection, model installation, translation, history, and cache tasks so the UI remains responsive.
- Continuous-cycle timing, confidence, route, cache hits, average latency, and skipped-busy-tick metrics.
- Non-blocking rotating error logs that never include recognized or translated text by default.
- JSON persistence with corrupt-file recovery.
- First-run language and privacy wizard.
- Configurable native Windows global shortcuts.
- Safe lens click-through mode with shortcut, panel, and tray recovery paths.
- System tray controls and optional tray startup.
- Dark and light themes, detected-text visibility, and translation font sizing.
- Translation-history search, copy, deletion, clearing, TXT export, and JSON export.
- Installed-model management with on-demand route installation and model removal.
- English Settings and About dialogs.
- Reproducible Windows `onedir` packaging with product metadata and the Translator Lens icon.
- Portable ZIP delivery with a SHA-256 checksum and bundled offline sentence-splitting models.

## Requirements

- 64-bit Windows 10 or Windows 11.
- Python 3.11 recommended.
- Administrator privileges are not required.

## Installation and execution

### Portable Windows package

1. Download `BeeTales-Translator-Lens-0.6.1-Windows-x64.zip` and its `.sha256` file.
2. Optionally verify the archive with `Get-FileHash .\BeeTales-Translator-Lens-0.6.1-Windows-x64.zip -Algorithm SHA256`.
3. Extract the complete ZIP to a writable folder.
4. Run `BeeTalesTranslatorLens.exe` inside the extracted `BeeTales Translator Lens` folder.

Keep the executable beside its `_internal` folder. The package is currently unsigned, so Windows SmartScreen may ask for confirmation. See [DISTRIBUTION.md](DISTRIBUTION.md) for release and troubleshooting details.

### Source installation

Open PowerShell in the repository and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Alternatively:

```powershell
.\scripts\create_venv.ps1
.\.venv\Scripts\python.exe main.py
```

If PowerShell blocks environment activation, run `.\.venv\Scripts\python.exe main.py` directly. The project supports repository paths that contain spaces.

## Using BeeTales Translator Lens

1. Position and resize the lens over the content to read.
2. Select a source language, or choose **Automatic** for Lingua detection after OCR.
3. Select a different target language and choose the capture interval, sensitivity, and preprocessing profile.
4. Press **Start** and approve the initial PaddleOCR model download if required.
5. When a translation route is missing, approve the requested Argos model download. BeeTales prefers a direct package and otherwise uses an English pivot.
6. Use **Force read**, **Pause**, **Resume**, **Swap**, **Copy**, **Clear**, and **Lock lens** as needed.
7. Leave **Save translation history** disabled for memory-only operation, or enable it to store text locally.
8. Optionally enable **Persistent translation cache** to reuse cached results after restarting. It is available only while history storage is enabled.
9. Use **Clear saved data** to remove both the saved history and persistent cache.
10. Open **Settings** to change the theme, translation font, startup behavior, and global shortcuts.
11. Use **History** to search, copy, delete, clear, or export saved translations.
12. Use **Models** to inspect installed Argos packages, install a language route, or remove a package.
13. Enable **Click-through** when you need mouse input to reach the application below the lens. Press **Ctrl+Shift+X**, use the visible panel, or use the tray menu to disable it.

Manual source selection remains preferable for very short messages and gives PaddleOCR the most appropriate recognition model. In Automatic mode, OCR currently begins with the English recognition model and Lingua detects the language from the recognized text.

## Local pipeline

```text
Capture the physical lens interior
-> Detect a changed or forced frame
-> Preprocess the image
-> Recognize text with local PaddleOCR
-> Normalize text and optionally detect its language with Lingua
-> Resolve an installed direct or English-pivot route
-> Read from the in-memory cache or translate with local Argos models
-> Update the interface on the Qt main thread
```

Only one pipeline cycle can be active. Timer events are discarded while a cycle is still processing instead of being queued.

## Continuous processing and performance

The selected interval controls how often BeeTales checks the lens. A lightweight grayscale comparison prevents OCR when the frame is static, while periodic forced reads protect against very small changes. If OCR or translation takes longer than the interval, the next timer tick is counted and skipped rather than queued.

The capture preview also reveals diagnostic metrics. These include the most recent stage timings, average complete-cycle time, translation-cache hits, and timer ticks skipped because the pipeline was busy. No image or recognized text is included in these metrics or logs.

## Default global shortcuts

```text
Ctrl+Shift+T  Show or hide BeeTales
Ctrl+Shift+P  Pause or resume
Ctrl+Shift+C  Copy the translation
Ctrl+Shift+L  Lock or unlock the lens
Ctrl+Shift+R  Force a new read
Ctrl+Shift+X  Toggle lens click-through
```

Shortcuts can be edited or disabled in **Settings**. They are temporarily unregistered while the Settings dialog is open, preventing an edited shortcut from activating an application action.

## Models, storage, and privacy

Settings and models use per-user folders similar to:

```text
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\config\settings.json
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\models\paddlex
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\models\argos
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\history\translations.json
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\cache\translations.json
%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\logs\beetales.log
```

Print the exact application data directory with:

```powershell
python -c "from beetales_translator_lens.storage.paths import data_directory; print(data_directory())"
```

BeeTales has no telemetry. Screenshots always remain in memory and are never added to history. Recognized and translated text also remain in memory unless the user explicitly enables local history. Persistent cache is automatically disabled when history is disabled. **Clear saved data** deletes both text stores. Log files contain operational messages and errors, not captured text. Network access is only needed to download OCR or translation model files after confirmation; inference is local afterward. Translation models are installed per language direction, so `en -> es` and `es -> en` are separate packages.

## Automated tests

Run:

```powershell
python -m pytest
```

The suite covers settings, geometry, multi-monitor capture, change detection, preprocessing, OCR parsing and caching, language detection, text normalization, direct and pivot route selection, translation caching, history limits and recovery, persistent-cache invalidation, performance counters, Argos translation behavior, and model installation decisions.

## Windows package build

Install the pinned packaging dependency and build the portable release:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

The script creates the `dist\BeeTales Translator Lens` folder, the versioned ZIP in `release`, and a SHA-256 sidecar. The verified Phase 7 build measures approximately **1.05 GiB extracted** and **450 MiB compressed**. OCR, language detection, Qt, and local inference runtimes account for most of that size; downloaded OCR and translation models remain in the per-user data folder and are not duplicated inside the ZIP.

## Manual Phase 6 test

1. Start the application and place the lens over an English sentence.
2. Select English as the source and Spanish as the target, then press **Start**.
3. Approve required local model downloads and confirm that translated text appears without freezing the UI.
4. Force-read the same text and confirm that a cache hit is reported without another translation.
5. Change the sentence and confirm that another local translation is produced.
6. Test **Automatic** with a sentence of at least several words and confirm the detected-language confidence appears.
7. Test **Swap** with two explicit languages and confirm a new route is selected.
8. Test a pair without a direct model and confirm that an English-pivot route is offered when available.
9. Test Polish, Portuguese, Japanese, and Spanish OCR manually with suitable preprocessing profiles.
10. Select a fast interval, leave the lens over rapidly changing text, and confirm busy timer ticks are skipped rather than accumulated.
11. Pause and confirm processing stops; resume and confirm one immediate forced read occurs.
12. Enable history and persistent cache, translate two different messages, restart, and confirm cached translation reuse.
13. Disable history, translate another message, and confirm no new text is written to either persistent file.
14. Press **Clear saved data** and confirm the history and persistent-cache files are removed.
15. Disconnect from the network after installing the models and confirm capture, OCR, detection, and translation still work.
16. Complete the first-run wizard and confirm its language selection is restored after restarting.
17. Test each global shortcut while another application has focus.
18. Enable click-through and confirm the underlying application receives mouse input; then recover using the shortcut, panel, and tray menu.
19. Test tray show/hide, pause/resume, Settings, History, Models, About, and Quit actions.
20. Switch between dark and light themes, change translation font size, and hide detected text.
21. Search history, copy and delete one entry, then export TXT and JSON files.
22. Inspect installed models, install one required route, and remove a disposable model if available.
23. Enable tray startup, restart, and confirm the application remains accessible from the tray.

## Repository structure

```text
BeeTales Translator Lens/
|-- main.py
|-- beetales_translator_lens/
|   |-- capture/
|   |-- ocr/
|   |-- platform/
|   |-- storage/
|   |-- translation/
|   |-- ui/
|   `-- workers/
|-- tests/
|-- scripts/
`-- packaging/
```

The importable package is `beetales_translator_lens`. The visible product name remains **BeeTales Translator Lens**.

## Roadmap

1. **Phase 1 — Floating interface:** complete.
2. **Phase 2 — Regional capture:** complete.
3. **Phase 3 — OCR:** complete.
4. **Phase 4 — Translation:** complete.
5. **Phase 5 — Continuous processing:** complete.
6. **Phase 6 — User experience:** complete.
7. **Phase 7 — Distribution:** complete.

The development environment is intentionally larger than the final release because it includes Python tooling, test dependencies, caches, temporary build files, and downloaded models. The final package excludes development-only files and optional Torch, Stanza, and SpaCy integrations. The `.venv` and `build` directories can be removed and recreated later; `dist` and `release` contain the usable deliverables.

## Implementation references

- [PaddleOCR 3.x local OCR pipeline](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/OCR.html)
- [PaddleOCR supported language codes](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html)
- [PaddlePaddle CPU installation on Windows](https://www.paddlepaddle.org.cn/documentation/docs/en/install/pip/windows-pip-en.html)
- [Argos Translate](https://github.com/argosopentech/argos-translate)
- [Lingua language detector](https://github.com/pemistahl/lingua-py)

## License

MIT. See [LICENSE](LICENSE).
