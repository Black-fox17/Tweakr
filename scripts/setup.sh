#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to determine the correct Python command (python or python3)
get_python_command() {
    if command_exists python && python --version 2>&1 | grep -q "Python 3"; then
        echo "python"
    elif command_exists python3; then
        echo "python3"
    else
        echo "Python 3 is not installed. Please install Python 3 to continue."
        exit 1
    fi
}

# Get the correct Python command
PYTHON_CMD=$(get_python_command)

# Check for Poetry
if command_exists poetry; then
    echo "Poetry detected. Setting up environment with Poetry..."
    
    # Install dependencies with Poetry
    poetry install --no-root
    
    # Download SpaCy model
    echo "Downloading SpaCy 'en_core_web_sm' model..."
    poetry run $PYTHON_CMD -m spacy download en_core_web_sm
    
    # Run the application
    poetry run $PYTHON_CMD app/main.py
else
    echo "Poetry not found. Falling back to venv or virtualenv..."
    
    # Check if virtualenv or venv is available
    if command_exists virtualenv; then
        echo "Using virtualenv to set up the environment..."
        virtualenv venv
    else
        echo "Using venv (built-in) to set up the environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    if [ -f requirements.txt ]; then
        echo "Installing dependencies..."
        pip install -r requirements.txt
    else
        echo "requirements.txt not found!"
        deactivate
        exit 1
    fi
    
    # Download SpaCy model
    echo "Downloading nlkt punkt model..."
    $PYTHON_CMD -m nltk.downloader punkt

fi
