# Jira Daily PM Radar - Bootstrap Script for PowerShell
# Usage: iwr -useb https://raw.githubusercontent.com/letya999/jira-daily-pm-radar/main/scripts/bootstrap.ps1 | iex

param (
    [string]$Dir = ".\jira-daily-pm-radar"
)

$ErrorActionPreference = "Stop"

Write-Host "Checking for git..."
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Warning "git is not installed. Please install git (e.g., 'winget install Git.Git') and restart PowerShell."
    exit 1
}

if (Test-Path $Dir) {
    Write-Host "Directory $Dir already exists. Updating..."
    Push-Location $Dir
    git pull
    Pop-Location
} else {
    Write-Host "Cloning Jira Daily PM Radar into $Dir..."
    git clone https://github.com/letya999/jira-daily-pm-radar.git $Dir
}

# Register with skills CLI
Write-Host "Registering skill with skills CLI..."
if (Get-Command npx -ErrorAction SilentlyContinue) {
    npx skills add -g letya999/jira-daily-pm-radar
} else {
    Write-Warning "npx not found. Skipping global skill registration."
}

$setupScript = Join-Path $Dir "scripts\setup.ps1"
if (Test-Path $setupScript) {
    & powershell -ExecutionPolicy Bypass -File $setupScript
} else {
    Write-Error "Error: $setupScript not found."
    exit 1
}
