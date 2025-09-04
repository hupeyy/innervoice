# setup_python.ps1
param(
    [string]$RequiredPythonVersion = "3.11"
)

Write-Host "🐍 Setting up Python environment for InnerVoice..." -ForegroundColor Green

try {
    # Check if Python is installed and get version
    try {
        $pythonOutput = python --version 2>&1
        Write-Host "Found: $pythonOutput" -ForegroundColor Cyan
        
        # Extract version number
        $versionMatch = [regex]::Match($pythonOutput, "Python (\d+\.\d+)")
        if ($versionMatch.Success) {
            $currentVersion = [System.Version]$versionMatch.Groups[1].Value
            $requiredVersion = [System.Version]$RequiredPythonVersion
            
            if ($currentVersion -lt $requiredVersion) {
                Write-Warning "Python $RequiredPythonVersion+ recommended (found $($currentVersion))"
                Write-Host "Consider upgrading for better compatibility" -ForegroundColor Yellow
            }
        }
    }
    catch {
        Write-Error "❌ Python not found! Please install Python $RequiredPythonVersion+ first."
        Write-Host "Download from: https://python.org/downloads/" -ForegroundColor Yellow
        exit 1
    }

    # Define paths
    $venvPath = "venv"
    $pipPath = "venv\Scripts\pip.exe"
    $reqPath = "requirements.txt"

    # Create virtual environment if needed
    if (!(Test-Path $venvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
        Write-Host "✅ Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "✅ Virtual environment exists" -ForegroundColor Green
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to activate virtual environment"
    }

    # Upgrade pip first
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    & $pipPath install --upgrade pip -q

    # Install packages
    if (Test-Path $reqPath) {
        Write-Host "Installing from requirements.txt..." -ForegroundColor Yellow
        & $pipPath install -r $reqPath
        
        if ($LASTEXITCODE -ne 0) {
            throw "Package installation failed"
        }
        
        Write-Host "✅ Packages installed successfully" -ForegroundColor Green
    } else {
        Write-Host "Installing essential packages..." -ForegroundColor Yellow
        $essentialPackages = @(
            "fastapi==0.116.1",
            "uvicorn==0.35.0", 
            "openai==1.105.0",
            "python-dotenv==1.0.0",
            "pycryptodome==3.23.0",
            "sqlalchemy==2.0.23",
            "python-multipart==0.0.20"
        )
        
        foreach ($package in $essentialPackages) {
            Write-Host "Installing $package..." -ForegroundColor Cyan
            & $pipPath install $package
        }
        
        # Generate requirements.txt
        Write-Host "Generating requirements.txt..." -ForegroundColor Yellow
        & $pipPath freeze > $reqPath
        Write-Host "✅ requirements.txt created" -ForegroundColor Green
    }

    # Verify installation
    Write-Host "Verifying installation..." -ForegroundColor Yellow
    $installedPackages = & $pipPath list --format=freeze
    $keyPackages = @("fastapi", "uvicorn", "openai", "sqlalchemy")
    
    foreach ($pkg in $keyPackages) {
        if ($installedPackages -match $pkg) {
            Write-Host "  ✅ $pkg installed" -ForegroundColor Green
        } else {
            Write-Warning "  ⚠️  $pkg not found"
        }
    }

    Write-Host "`n🎉 Python setup complete! Run 'npm run dev' to start." -ForegroundColor Green

} catch {
    Write-Error "❌ Setup failed: $_"
    Write-Host "💡 Try: Remove 'venv' folder and run again" -ForegroundColor Yellow
    exit 1
}