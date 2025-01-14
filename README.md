# Research Paper Reference Assistant

## Overview
This Streamlit application helps researchers generate references and in-text citations for their research paper drafts by matching keywords with a database of papers.

## Features
- Upload research paper drafts (Word .docx or .txt)
- Select research categories
- Automatically match keywords
- Generate APA-style references
- Add in-text citations
- Download modified document

## Prerequisites
- Python 3.8+
- Streamlit
- SQLAlchemy
- python-docx
- Other dependencies in `requirements.txt`

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd research-paper-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following:
```
DATABASE_URI=your_sqlalchemy_database_connection_string
MONGODB_URI=your_mongodb_connection_string
```

## Running the Application
```bash
streamlit run app.py
```

## Usage
1. Upload your research paper draft
2. Select relevant research categories
3. Click "Generate References & Citations"
4. Review matching papers and references
5. Download the modified document

## Configuration
- Customize reference and citation styles in the respective generator classes
- Modify category fetching in the `_fetch_categories` method

## Troubleshooting
- Ensure all dependencies are installed
- Check database connection strings
- Verify file upload permissions

## Contributing
- Fork the repository
- Create a feature branch
- Submit a pull request

## License
[Specify your license]

## Contact
[Your contact information]