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

# Start Streamlit server
streamlit run datapipeline/streamlit_app.py --server.port 5000 --server.address 0.0.0.0
