#!/bin/bash
# For local development. Production use: uvx --from git+https://github.com/letya999/jira-daily-pm-radar.git

# Jira Daily PM Radar - Setup Python environment

set -e

echo "Setting up Jira Daily PM Radar Python environment..."

# 1. OS Detection
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM=linux;;
    Darwin*)    PLATFORM=darwin;;
    *)          echo "Unsupported OS: ${OS}"; exit 1;;
esac

# 2. Check Python >= 3.12
echo "Checking Python version..."
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=python
else
    echo "Error: Python is not installed. Please install Python 3.12 or newer."
    exit 1
fi

$PYTHON_CMD -c "import sys; assert sys.version_info >= (3,12), f'Error: Python 3.12+ required, found {sys.version}'"

# 3. Check/Install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Source uv for the current session
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv installation failed or not in PATH."
    exit 1
fi

# 4. Sync project dependencies
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Syncing project dependencies in $PROJECT_DIR..."
cd "$PROJECT_DIR"
uv sync --extra mcp

echo "---------------------------------------------------"
echo "SUCCESS: Python environment setup complete!"
echo "Project directory: $PROJECT_DIR"
echo "---------------------------------------------------"
