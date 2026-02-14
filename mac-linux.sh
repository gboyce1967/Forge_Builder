#!/bin/bash
# Forge Builder Launcher for Linux and macOS
# Installs requirements and runs the script

set -e

echo "========================================"
echo "   Forge Builder - Setup & Launch"
echo "========================================"
echo

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="Unknown";;
esac
echo "[*] Detected platform: $PLATFORM"

# Check for Python 3
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null; then
    # Check if 'python' is Python 3
    if python --version 2>&1 | grep -q "Python 3"; then
        PYTHON=python
    else
        echo "[ERROR] Python 3 is required but not found."
        echo "        Install Python 3.6+ from https://www.python.org/downloads/"
        exit 1
    fi
else
    echo "[ERROR] Python is not installed."
    echo "        Install Python 3.6+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[*] Using Python: $($PYTHON --version)"

# Check for pip
if ! $PYTHON -m pip --version &> /dev/null; then
    echo "[ERROR] pip is not installed."
    echo "        Install pip: $PYTHON -m ensurepip --upgrade"
    exit 1
fi

# Install requirements
echo "[*] Checking dependencies..."
if ! $PYTHON -c "import reportlab" &> /dev/null; then
    echo "[*] Installing reportlab..."
    $PYTHON -m pip install --user reportlab
else
    echo "[*] reportlab already installed"
fi

echo
echo "[*] Launching Forge Designer..."
echo "========================================"
echo

# Run the script, passing through any arguments
$PYTHON "$(dirname "$0")/ForgeDesigner.py" "$@"
