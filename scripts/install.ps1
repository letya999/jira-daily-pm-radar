# Jira Daily PM Radar - Legacy Installer Wrapper for PowerShell
# This script is deprecated. Use 'npx skills add' for registration 
# and 'scripts/setup.ps1' for Python environment setup.

Write-Host "-------------------------------------------------------------------" -ForegroundColor Yellow
Write-Host "WARNING: scripts/install.ps1 is DEPRECATED." -ForegroundColor Yellow
Write-Host "Recommended way to install:" -ForegroundColor Yellow
Write-Host "1. Register globally: npx skills add -g letya999/jira-daily-pm-radar" -ForegroundColor Yellow
Write-Host "2. Setup environment: powershell -File scripts/setup.ps1" -ForegroundColor Yellow
Write-Host "-------------------------------------------------------------------" -ForegroundColor Yellow

# Fallback: run setup.ps1 to ensure environment is ready
$setupScript = Join-Path $PSScriptRoot "setup.ps1"
if (Test-Path $setupScript) {
    & powershell -ExecutionPolicy Bypass -File $setupScript
} else {
    Write-Error "Error: scripts/setup.ps1 not found."
    exit 1
}
