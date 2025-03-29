import pandas as pd
from app.core.database import engine
# csv_file = "papers_data.csv"
# df = pd.read_csv(csv_file)

# # Write data to PostgreSQL
# df.to_sql("papers", engine, if_exists="append", index=False)
import csv
from sqlalchemy.orm import Session
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers

def save_all_papers_to_csv(filename="papers_data.csv"):
    with get_session_with_ctx_manager() as session:
        # Fetch all papers
        papers = session.query(Papers).all()

        # Convert SQLAlchemy objects to dictionary
        papers_list = [paper.__dict__ for paper in papers]

        # Remove private SQLAlchemy attributes (e.g., `_sa_instance_state`)
        for paper in papers_list:
            paper.pop("_sa_instance_state", None)

        # Extract fieldnames dynamically
        keys = papers_list[0].keys() if papers_list else []

        # Write to CSV
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=keys)
            writer.writeheader()
            writer.writerows(papers_list)

        print(f"Data saved to {filename}")
save_all_papers_to_csv()