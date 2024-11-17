from datetime import datetime
from sqlalchemy.orm import Session
import os
from PyPDF2 import PdfReader

from core.openai import extract_keywords, generate_embedding
from core.pinecone import pinecone_index
from core.database import SessionLocal, Document
from core.upload_to_s3 import upload_to_s3

def process_document(file_path, category):
    # Extract text from PDF
    reader = PdfReader(file_path)
    text = " ".join([page.extract_text() for page in reader.pages])

    # Extract metadata (simulate for demo purposes)
    title = os.path.basename(file_path).replace(".pdf", "")
    pub_date = datetime.now().date()  # Replace with actual date if available

    # Extract keywords
    keywords = extract_keywords(text)

    # Generate embedding
    embedding = generate_embedding(text)

    # Store in Pinecone
    pinecone_index.upsert([(title, embedding)])

    # Upload content to S3
    s3_location = upload_to_s3(file_path, f"{title}.pdf")

    # Store metadata in PostgreSQL
    db_session = SessionLocal()
    document = Document(
        title=title,
        category=category,
        pub_date=pub_date,
        keywords=keywords,
    )
    db_session.add(document)
    db_session.commit()
    db_session.close()

    print(f"Processed and stored document: {title}")
    return s3_location
