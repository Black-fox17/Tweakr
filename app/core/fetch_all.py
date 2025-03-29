import pandas as pd
from database import engine
csv_file = "papers_data.csv"
df = pd.read_csv(csv_file)

# Write data to PostgreSQL
df.to_sql("papers", engine, if_exists="append", index=False)

print("Data successfully written to PostgreSQL!")