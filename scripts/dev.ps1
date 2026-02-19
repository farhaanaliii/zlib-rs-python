# zlib-rs-python development script (Windows PowerShell)
# Usage: .\scripts\dev.ps1 <command>

param(
    [Parameter(Position=0)]
    [ValidateSet("build", "build-debug", "test", "bench", "clean", "all", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"

function Write-Header($msg) {
    Write-Host ""
    Write-Host "=== $msg ===" -ForegroundColor Cyan
    Write-Host ""
}

function Invoke-Build {
    Write-Header "Building (release)"
    $env:RUSTFLAGS = "-C target-cpu=native"
    maturin develop --release
}

function Invoke-BuildDebug {
    Write-Header "Building (debug)"
    maturin develop
}

function Invoke-Test {
    Write-Header "Running tests"
    pytest tests/ -v
}

function Invoke-Bench {
    Write-Header "Running benchmarks"
    python benchmarks/bench_zlib.py
}

function Invoke-Clean {
    Write-Header "Cleaning build artifacts"
    if (Test-Path "target") { Remove-Item -Recurse -Force "target" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    Get-ChildItem -Recurse -Filter "__pycache__" -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter "*.egg-info" -Directory | Remove-Item -Recurse -Force
    Write-Host "Done." -ForegroundColor Green
}

function Invoke-All {
    Invoke-Build
    Invoke-Test
    Invoke-Bench
}

function Show-Help {
    Write-Host ""
    Write-Host "zlib-rs-python development script" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Usage: .\scripts\dev.ps1 <command>" -ForegroundColor White
    Write-Host ""
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  build        Build release version with native CPU optimizations"
    Write-Host "  build-debug  Build debug version (faster compile)"
    Write-Host "  test         Run tests with pytest"
    Write-Host "  bench        Run performance benchmarks"
    Write-Host "  clean        Remove build artifacts"
    Write-Host "  all          Build (release) + test + benchmark"
    Write-Host "  help         Show this help message"
    Write-Host ""
}

switch ($Command) {
    "build"       { Invoke-Build }
    "build-debug" { Invoke-BuildDebug }
    "test"        { Invoke-Test }
    "bench"       { Invoke-Bench }
    "clean"       { Invoke-Clean }
    "all"         { Invoke-All }
    "help"        { Show-Help }
}
