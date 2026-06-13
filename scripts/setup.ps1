# For local development. Production use: uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git
# Jira Daily PM Radar - Setup Python environment for Windows

$ErrorActionPreference = "Stop"

Write-Host "Setting up Jira Daily PM Radar Python environment..." -ForegroundColor Cyan

# 1. Check Python >= 3.12
Write-Host "Checking Python version..."
$pythonCmd = "python"
if (!(Get-Command python -ErrorAction SilentlyContinue)) {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $pythonCmd = "py"
    } else {
        Write-Error "Python is not installed. Please install Python 3.12 or newer (e.g., 'winget install Python.Python.3.12')."
        exit 1
    }
}

try {
    if ($pythonCmd -eq "py") {
        & py -3.12 -c "import sys; exit(0) if sys.version_info >= (3,12) else exit(1)"
    } else {
        & python -c "import sys; exit(0) if sys.version_info >= (3,12) else exit(1)"
    }
} catch {
    Write-Error "Python 3.12+ is required."
    exit 1
}

# 2. Check/Install uv
if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Installing uv..."
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "User") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "Machine")
}

if (!(Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "uv installation failed or not in PATH."
    exit 1
}

# 3. Sync project dependencies
$projectDir = $PSScriptRoot
if ($projectDir -eq "") { $projectDir = Get-Location }
$projectDir = (Get-Item (Join-Path $projectDir "..")).FullName

Write-Host "Syncing project dependencies in $projectDir..."
Push-Location $projectDir
try {
    uv sync --extra mcp
} finally {
    Pop-Location
}

Write-Host "---------------------------------------------------" -ForegroundColor Green
Write-Host "SUCCESS: Python environment setup complete!" -ForegroundColor Green
Write-Host "Project directory: $projectDir"
Write-Host "---------------------------------------------------" -ForegroundColor Green
