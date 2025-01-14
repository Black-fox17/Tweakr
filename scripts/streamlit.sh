#!/bin/bash

# Get the current working directory
CURRENT_DIR=$(pwd)

# Define the directories to add to PYTHONPATH
APP_DIR="$CURRENT_DIR"
DATAPIPELINE_DIR="$CURRENT_DIR/datapipeline"
APPSEC_DIR="$CURRENT_DIR/app"

# Export PYTHONPATH dynamically
export PYTHONPATH="$APP_DIR:$DATAPIPELINE_DIR:$APPSEC_DIR:$PYTHONPATH"

# Print the PYTHONPATH for debugging
echo "PYTHONPATH set to: $PYTHONPATH"

# Optionally, run Streamlit with the dynamically set PYTHONPATH
streamlit run "$APP_DIR/app/app.py"
