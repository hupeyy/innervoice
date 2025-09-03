# run_backend.ps1

# Change to the project directory
Set-Location $PSScriptRoot

# Activate the virtual environment
& ".\backend\venv\Scripts\Activate.ps1"

# Run the backend server
python .\backend\main.py