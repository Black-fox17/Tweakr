#!/bin/bash
apt-get update
apt-get install -y libreoffice
# Install Python dependencies
pip install -r requirements.txt

# Install spaCy model
python -m spacy download en_core_web_sm