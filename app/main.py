
from app.core.references_generator import ReferenceGenerator
from datapipeline.core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
from app.core.intext_citation import InTextCitationProcessor
from app.core.paper_matcher import PaperKeywordMatcher



if __name__ == "__main__":
    matcher = PaperKeywordMatcher()
    file_path = "/Users/naija/Documents/gigs/tweakr/tweakr-mvp/test_docs/testdoc.docx"
    output_doc = "/Users/naija/Documents/gigs/tweakr/tweakr-mvp/test_docs/testdoc_with_citations.docx"
    category = "quantum_physics"
    matching_titles = matcher.match_keywords(file_path, category)

    relevant_papers = []
    if matching_titles:
        print("Matching Papers:")
        for title in matching_titles:
            print(f"- {title}")
            relevant_papers.append(title)

        reference_generator = ReferenceGenerator(style="APA")
        references = reference_generator.generate_references(matching_titles, category)

        print("\nReferences:")
        for reference in references:
            print(f"- {reference}")
        try:
            intext_citation = InTextCitationProcessor(style="APA", collection_name="quantum_physics")
            modified_file_path = intext_citation.process_sentences(file_path, output_doc)
            print(f"Modified draft saved to: {modified_file_path}")
        except Exception as e:
            print(f"Error processing draft: {e}")
    else:
        print("No matching papers found.")
