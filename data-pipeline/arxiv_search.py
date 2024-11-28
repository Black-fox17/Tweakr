import os
import arxiv
from arxiv import Client, Search, SortCriterion

# Ensure the target directory exists
os.makedirs('./store', exist_ok=True)

# Construct the default API client.
client = Client()

# Search for the 10 most recent articles matching the keyword "quantum."
search = Search(
    query="quantum",
    max_results=10,
    sort_by=SortCriterion.SubmittedDate
)

# Initialize an empty list to store results
all_results = []

# Iterate over the results generator once
for result in client.results(search):
    print(result.title)
    # Sanitize the title to create a valid filename
    sanitized_title = "".join(
        [c if c.isalnum() or c in (' ', '.', '_') else "_" for c in result.title]
    )
    filename = f"{sanitized_title}.pdf"
    # Download the PDF to the specified directory with the sanitized filename
    result.download_pdf(dirpath="./store", filename=filename)
    # Append the result to the list
    all_results.append(result)

# Now, all_results contains all the fetched results
print([r.title for r in all_results])
