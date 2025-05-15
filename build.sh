 apt-get update
 apt-get install -y libreoffice
 # Find LibreOffice install directory
 LIBREOFFICE_PATH=$(dirname $(which soffice))
 # Add LibreOffice to PATH (append to existing PATH)
 echo "Adding $LIBREOFFICE_PATH to PATH"
 export PATH="$PATH:$LIBREOFFICE_PATH"

 # Print the PATH to confirm
 echo "Current PATH: $PATH"

 pip install -r requirements.txt
 python -m spacy download en_core_web_sm