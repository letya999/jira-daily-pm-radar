#!/bin/bash

# Jira Daily PM Radar - Bootstrap Script
# Usage: curl -LsSf https://raw.githubusercontent.com/letya999/jira-daily-pm-radar/main/scripts/bootstrap.sh | bash

set -e

# Default directory
TARGET_DIR="./jira-daily-pm-radar"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --dir) TARGET_DIR="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo "Checking for git..."
if ! command -v git >/dev/null 2>&1; then
    echo "Error: git is not installed. Please install git first."
    exit 1
fi

if [ -d "$TARGET_DIR" ]; then
    echo "Directory $TARGET_DIR already exists. Updating..."
    cd "$TARGET_DIR"
    git pull
else
    echo "Cloning Jira Daily PM Radar into $TARGET_DIR..."
    git clone https://github.com/letya999/jira-daily-pm-radar.git "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

# Register with skills CLI
echo "Registering skill with skills CLI..."
if command -v npx >/dev/null 2>&1; then
    npx skills add -g letya999/jira-daily-pm-radar
else
    echo "Warning: npx not found. Skipping global skill registration."
fi

# Run the setup for Python environment
if [ -f "scripts/setup.sh" ]; then
    bash scripts/setup.sh
else
    echo "Error: scripts/setup.sh not found in $TARGET_DIR"
    exit 1
fi
