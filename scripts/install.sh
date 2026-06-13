#!/bin/bash

# Jira Daily PM Radar - Legacy Installer Wrapper
# This script is deprecated. Use 'npx skills add' for registration 
# and 'scripts/setup.sh' for Python environment setup.

echo "-------------------------------------------------------------------"
echo "WARNING: scripts/install.sh is DEPRECATED."
echo "Recommended way to install:"
echo "1. Register globally: npx skills add -g letya999/jira-daily-pm-radar"
echo "2. Setup environment: bash scripts/setup.sh"
echo "-------------------------------------------------------------------"

# Fallback: run setup.sh to ensure environment is ready
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/setup.sh" ]; then
    bash "$SCRIPT_DIR/setup.sh"
else
    echo "Error: scripts/setup.sh not found."
    exit 1
fi
