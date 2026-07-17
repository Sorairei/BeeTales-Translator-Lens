$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    throw ".venv was not found. Run scripts\create_venv.ps1 first."
}

& ".\.venv\Scripts\python.exe" -m PyInstaller "packaging\beetales_translator_lens.spec" --noconfirm
