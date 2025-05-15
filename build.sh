#!/bin/bash
# setup_environment.sh - Install dependencies for document classification

# Exit on any error
set -e

echo "=== Installing System Dependencies ==="
apt-get update
apt-get install -y libreoffice python3-pip

# Verify LibreOffice installation
if command -v libreoffice &>/dev/null; then
    echo "LibreOffice installed successfully"
    libreoffice --version
else
    echo "ERROR: LibreOffice installation failed"
    exit 1
fi

# Add LibreOffice to PATH if needed
LIBREOFFICE_PATH=$(dirname $(which libreoffice))
echo "Adding $LIBREOFFICE_PATH to PATH"
export PATH="$PATH:$LIBREOFFICE_PATH"
echo "Current PATH: $PATH"

echo "=== Installing Python Dependencies ==="

# Install Python dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm

echo "=== Environment Setup Complete ==="
echo "Run your classification script with: python document_classifier.py your_document.docx"