$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $root

if (-not (Test-Path .venv)) {
    Write-Host "Creating virtual environment..."
    py -3 -m venv .venv
}

Write-Host "Activating venv and installing dependencies..."
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Starting Snipping Tool (Python)..."
python -m snipping_tool.app
