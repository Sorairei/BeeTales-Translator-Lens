# BeeTales Translator Lens

BeeTales Translator Lens is a privacy-focused Windows desktop application that recognizes and translates text underneath a floating screen lens. Capture, OCR, language detection, and translation run locally after the required models have been downloaded.

## Project status

**Phase 5 — Continuous processing** is implemented.

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

## Requirements

- 64-bit Windows 10 or Windows 11.
- Python 3.11 recommended.
- Administrator privileges are not required.

## Installation and execution

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

## Using Phase 5

1. Position and resize the lens over the content to read.
2. Select a source language, or choose **Automatic** for Lingua detection after OCR.
3. Select a different target language and choose the capture interval, sensitivity, and preprocessing profile.
4. Press **Start** and approve the initial PaddleOCR model download if required.
5. When a translation route is missing, approve the requested Argos model download. BeeTales prefers a direct package and otherwise uses an English pivot.
6. Use **Force read**, **Pause**, **Resume**, **Swap**, **Copy**, **Clear**, and **Lock lens** as needed.
7. Leave **Save translation history** disabled for memory-only operation, or enable it to store text locally.
8. Optionally enable **Persistent translation cache** to reuse cached results after restarting. It is available only while history storage is enabled.
9. Use **Clear saved data** to remove both the saved history and persistent cache.

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

## Manual Phase 5 test

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
6. **Phase 6 — User experience:** first-run wizard, global shortcuts, system tray, click-through mode, and a full model-management interface.
7. **Phase 7 — Distribution:** optimized PyInstaller `onedir` build, metadata, icon, and portable ZIP.

The development environment is intentionally much larger than the final source repository because it includes Python, Qt, PaddlePaddle, Torch-related translation dependencies, language-detection data, and downloaded models. Phase 7 will measure the distributable build and exclude development-only files where compatibility permits.

## Implementation references

- [PaddleOCR 3.x local OCR pipeline](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/OCR.html)
- [PaddleOCR supported language codes](https://www.paddleocr.ai/latest/en/version3.x/algorithm/PP-OCRv5/PP-OCRv5_multi_languages.html)
- [PaddlePaddle CPU installation on Windows](https://www.paddlepaddle.org.cn/documentation/docs/en/install/pip/windows-pip-en.html)
- [Argos Translate](https://github.com/argosopentech/argos-translate)
- [Lingua language detector](https://github.com/pemistahl/lingua-py)

## License

MIT. See [LICENSE](LICENSE).
