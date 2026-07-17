# BeeTales Translator Lens for Windows

## Install the portable package

1. Keep the ZIP and its `.sha256` file together.
2. In PowerShell, run:

   ```powershell
   Get-FileHash .\BeeTales-Translator-Lens-0.6.0-Windows-x64.zip -Algorithm SHA256
   ```

3. Compare the displayed hash with the value in the `.sha256` file.
4. Extract the complete ZIP to a writable folder.
5. Run `BeeTalesTranslatorLens.exe` inside the extracted `BeeTales Translator Lens` folder.

Do not move the executable away from its `_internal` folder. BeeTales is portable as a folder, not as a single executable.

## Windows security notice

This release is not code-signed. Windows SmartScreen may show an unrecognized-app warning even when the SHA-256 value is correct. Only continue when the archive came from a trusted BeeTales release location and its checksum matches.

## Models and offline use

The application includes its runtime and sentence-splitting models. PaddleOCR and Argos translation models are installed per user after explicit confirmation because they vary by language. Once the required OCR and translation models are installed, capture, recognition, language detection, and translation run locally.

User data is stored under `%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens`. Removing the portable application folder does not remove settings, logs, history, cache, or downloaded models.

## Build a release from source

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_windows.ps1
```

The script recreates `build` and `dist`, then writes the versioned ZIP and SHA-256 sidecar to `release`. PyInstaller is pinned in `requirements-build.txt` to make the build toolchain auditable.

## Troubleshooting

- If the executable does not open, confirm that `_internal` is still beside it and re-extract the entire archive.
- If OCR or translation is unavailable, open **Models** and install the required route while connected to the internet.
- If the lens is invisible, use `Ctrl+Shift+T` or the system tray icon to show BeeTales.
- Operational logs are stored in `%LOCALAPPDATA%\BeeTales\BeeTales Translator Lens\logs` and do not contain recognized or translated text by default.
