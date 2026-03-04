# Backend\run.ps1
# One command to start backend reliably (creates venv if missing, installs deps, runs uvicorn)

$ErrorActionPreference = "Stop"

# Move to Backend folder (folder containing this script)
Set-Location $PSScriptRoot

# Create venv if missing
if (!(Test-Path ".\.venv\Scripts\python.exe")) {
    python -m venv .venv
}

# Upgrade pip + install requirements
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Run server
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000