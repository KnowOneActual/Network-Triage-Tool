#!/usr/bin/env bash
set -e

echo "========================================"
echo "Installing Network Triage Tool..."
echo "========================================"

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed."
    echo "Please install Python 3.11 or higher and try again."
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo "Error: git is required but not installed."
    exit 1
fi

INSTALL_DIR="$HOME/.network-triage"
REPO_URL="https://github.com/knowoneactual/Network-Triage-Tool.git"

if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation in $INSTALL_DIR..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "Cloning repository to $INSTALL_DIR..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo "Setting up virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

echo "Installing project and dependencies..."
pip install -e .

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "To run the tool from anywhere, you can add it to your PATH."
echo "Add the following line to your ~/.bashrc or ~/.zshrc:"
echo "export PATH=\"$INSTALL_DIR/.venv/bin:\$PATH\""
echo ""
echo "Or, simply run it now with:"
echo "$INSTALL_DIR/.venv/bin/network-triage"
echo ""
