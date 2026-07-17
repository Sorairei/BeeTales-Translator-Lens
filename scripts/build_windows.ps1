param(
    [switch]$SkipZip
)

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BuildPath = Join-Path $ProjectRoot "build"
$DistPath = Join-Path $ProjectRoot "dist"
$ReleasePath = Join-Path $ProjectRoot "release"
$AppDirectory = Join-Path $DistPath "BeeTales Translator Lens"
$Executable = Join-Path $AppDirectory "BeeTalesTranslatorLens.exe"
$ZipPath = Join-Path $ReleasePath "BeeTales-Translator-Lens-0.6.1-Windows-x64.zip"

if (-not (Test-Path -LiteralPath $Python)) {
    throw ".venv was not found. Run scripts\create_venv.ps1 first."
}

& $Python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller is not installed. Run: .\.venv\Scripts\python.exe -m pip install -r requirements-build.txt"
}

foreach ($Target in @($BuildPath, $DistPath)) {
    $Parent = Split-Path -Parent $Target
    if ($Parent -ne $ProjectRoot) {
        throw "Unsafe build cleanup target: $Target"
    }
    if (Test-Path -LiteralPath $Target) {
        Remove-Item -LiteralPath $Target -Recurse -Force
    }
}

& $Python -m PyInstaller (Join-Path $ProjectRoot "packaging\beetales_translator_lens.spec") --noconfirm --clean
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $Executable)) {
    throw "The PyInstaller build did not produce BeeTalesTranslatorLens.exe."
}

New-Item -ItemType Directory -Force -Path $ReleasePath | Out-Null
Copy-Item -LiteralPath (Join-Path $ProjectRoot "LICENSE") -Destination $AppDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot "THIRD_PARTY_NOTICES.md") -Destination $AppDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot "README.md") -Destination $AppDirectory
Copy-Item -LiteralPath (Join-Path $ProjectRoot "DISTRIBUTION.md") -Destination $AppDirectory

if (-not $SkipZip) {
    if (Test-Path -LiteralPath $ZipPath) {
        Remove-Item -LiteralPath $ZipPath -Force
    }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::CreateFromDirectory(
        $AppDirectory,
        $ZipPath,
        [System.IO.Compression.CompressionLevel]::Optimal,
        $true
    )
    $Hash = (Get-FileHash -LiteralPath $ZipPath -Algorithm SHA256).Hash
    Set-Content -LiteralPath "$ZipPath.sha256" -Value "$Hash  $(Split-Path -Leaf $ZipPath)" -Encoding ascii
}

$AppBytes = (Get-ChildItem -LiteralPath $AppDirectory -File -Recurse | Measure-Object Length -Sum).Sum
Write-Host "Build complete: $Executable"
Write-Host ("Onedir size: {0:N1} MiB" -f ($AppBytes / 1MB))
if (-not $SkipZip) {
    Write-Host ("Portable ZIP: {0} ({1:N1} MiB)" -f $ZipPath, ((Get-Item -LiteralPath $ZipPath).Length / 1MB))
}
