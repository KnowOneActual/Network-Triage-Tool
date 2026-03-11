$ErrorActionPreference = "Stop"

Write-Host "========================================"
Write-Host "Installing Network Triage Tool..."
Write-Host "========================================"

if (!(Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: Python is required but not installed." -ForegroundColor Red
    Write-Host "Please install Python 3.11 or higher from python.org and ensure 'Add to PATH' is checked." -ForegroundColor Red
    exit 1
}

if (!(Get-Command "git" -ErrorAction SilentlyContinue)) {
    Write-Host "Error: git is required but not installed." -ForegroundColor Red
    exit 1
}

$InstallDir = Join-Path $HOME ".network-triage"
$RepoUrl = "https://github.com/knowoneactual/Network-Triage-Tool.git"

if (Test-Path $InstallDir) {
    Write-Host "Updating existing installation in $InstallDir..."
    Set-Location $InstallDir
    git pull origin main
} else {
    Write-Host "Cloning repository to $InstallDir..."
    git clone $RepoUrl $InstallDir
    Set-Location $InstallDir
}

Write-Host "Setting up virtual environment..."
python -m venv .venv
& .venv\Scripts\Activate.ps1

Write-Host "Installing project and dependencies..."
pip install -e .

Write-Host ""
Write-Host "========================================"
Write-Host "Installation complete!"
Write-Host "========================================"
Write-Host ""
Write-Host "To run the tool from anywhere, you should add its directory to your PATH environment variable:"
Write-Host "$InstallDir\.venv\Scripts"
Write-Host ""
Write-Host "Or, simply run it now with:"
Write-Host "$InstallDir\.venv\Scripts\network-triage.exe"
Write-Host ""