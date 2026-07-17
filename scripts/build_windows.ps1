$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $ProjectRoot

if (-not (Test-Path -LiteralPath ".\.venv\Scripts\python.exe")) {
    throw "No se encontró .venv. Ejecuta primero scripts\create_venv.ps1."
}

& ".\.venv\Scripts\python.exe" -m PyInstaller "packaging\beetales_translator_lens.spec" --noconfirm
