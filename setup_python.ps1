# setup_python.ps1
Write-Host "🐍 Setting up Python environment for InnerVoice..." -ForegroundColor Green

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Install packages
if (Test-Path "requirements.txt") {
    Write-Host "Installing packages from requirements.txt..." -ForegroundColor Yellow
    pip install -r requirements.txt
} else {
    Write-Host "Installing essential packages..." -ForegroundColor Yellow
    pip install fastapi uvicorn openai python-dotenv pycryptodome
    pip freeze > requirements.txt
    Write-Host "Created requirements.txt" -ForegroundColor Green
}

Write-Host "✅ Python setup complete!" -ForegroundColor Green