param(
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$TestTempPath = Join-Path $ProjectRoot ".pytest-tmp"

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $VirtualEnvironmentPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if (Test-Path -LiteralPath $VirtualEnvironmentPython) {
        $PythonPath = $VirtualEnvironmentPython
    }
    else {
        $PythonPath = (Get-Command python -ErrorAction Stop).Source
    }
}

& $PythonPath -m pytest --basetemp $TestTempPath
if ($LASTEXITCODE -ne 0) {
    throw "The BeeTales test suite failed with exit code $LASTEXITCODE."
}
