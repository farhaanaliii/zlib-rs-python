# Release script for zlib-rs-python (Windows PowerShell)
#
# Usage:
#   .\scripts\release.ps1 <version>
#
# Example:
#   .\scripts\release.ps1 0.2.0
#
# This script will:
#   1. Update version in Cargo.toml and __init__.py
#   2. Build and test the release locally
#   3. Create a git tag and push it (triggers GitHub Actions release)

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

function Write-Header($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
    Write-Host ""
}

# Validate version format
if ($Version -notmatch '^\d+\.\d+\.\d+(-\w+(\.\d+)?)?$') {
    Write-Host "Error: Invalid version format '$Version'." -ForegroundColor Red
    Write-Host "Expected format: X.Y.Z or X.Y.Z-alpha.1" -ForegroundColor Red
    exit 1
}

Write-Header "Preparing release v$Version"

# 1. Update Cargo.toml version
Write-Header "1/5 Updating Cargo.toml"
$cargoToml = Get-Content "Cargo.toml" -Raw
$cargoToml = $cargoToml -replace 'version = "[^"]*"', "version = ""$Version"""
Set-Content "Cargo.toml" $cargoToml -NoNewline
Write-Host "Cargo.toml updated to $Version" -ForegroundColor Green

# 2. Update __init__.py version
Write-Header "2/5 Updating __init__.py"
$initPy = Get-Content "python\zlib_rs\__init__.py" -Raw
$initPy = $initPy -replace '__version__ = "[^"]*"', "__version__ = ""$Version"""
Set-Content "python\zlib_rs\__init__.py" $initPy -NoNewline
Write-Host "__init__.py updated to $Version" -ForegroundColor Green

# 3. Build release
Write-Header "3/5 Building release"
$env:RUSTFLAGS = "-C target-cpu=native"
maturin develop --release
if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne 1) {
    Write-Host "Build failed!" -ForegroundColor Red
    exit 1
}

# 4. Run tests
Write-Header "4/5 Running tests"
pytest tests/ -v
if ($LASTEXITCODE -ne 0) {
    Write-Host "Tests failed! Aborting release." -ForegroundColor Red
    exit 1
}

# 5. Show summary and prompt for confirmation
Write-Header "5/5 Ready to release"
Write-Host "Version:  v$Version" -ForegroundColor Yellow
Write-Host ""
Write-Host "This will:" -ForegroundColor White
Write-Host "  - Commit version bump" -ForegroundColor White
Write-Host "  - Create git tag v$Version" -ForegroundColor White
Write-Host "  - Push tag to origin (triggers CI release pipeline)" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "Proceed? (y/n)"
if ($confirm -ne "y") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# Commit, tag, and push
git add Cargo.toml python/zlib_rs/__init__.py
git commit -m "release: v$Version"
git tag -a "v$Version" -m "Release v$Version"
git push origin main
git push origin "v$Version"

Write-Host ""
Write-Host "=== Release v$Version pushed ===" -ForegroundColor Green
Write-Host ""
Write-Host "GitHub Actions will now:" -ForegroundColor White
Write-Host "  1. Build wheels for Linux, Windows, macOS" -ForegroundColor White
Write-Host "  2. Test wheels on all platforms" -ForegroundColor White
Write-Host "  3. Publish to PyPI" -ForegroundColor White
Write-Host "  4. Create GitHub Release" -ForegroundColor White
Write-Host ""
Write-Host "Monitor progress: https://github.com/farhaanaliii/zlib-rs-python/actions" -ForegroundColor Cyan
