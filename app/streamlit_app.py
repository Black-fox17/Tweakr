import os
import streamlit as st

import os
import sys

# Calculate the project root (assumes app/ is one level below the project root)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
print("Project Root: ", PROJECT_ROOT)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from app.core.extract_keywords import ExtractKeywords
from app.core.paper_matcher import PaperKeywordMatcher
from app.core.intext_citation import InTextCitationProcessor, ReferenceGenerator

# Load environment variables
load_dotenv()

class ResearchPaperAssistant:
    def __init__(self):
        # Cached categories
        self.categories = self._fetch_categories()
    
    def _fetch_categories(self):
        """
        Fetch unique categories from the database.
        Cached at application startup.
        """
        try:
            with get_session_with_ctx_manager() as session:
                categories = session.query(Papers.category).distinct().order_by(Papers.category).all()
                return [category[0] for category in categories]
        except Exception as e:
            st.error(f"Error fetching categories: {e}")
            return []

    def run(self):
        """
        Main Streamlit application
        """
        st.title("Research Paper Reference Assistant")
        
        # Sidebar for configuration
        st.sidebar.header("Upload Research Draft")
        
        # File uploader
        uploaded_file = st.sidebar.file_uploader(
            "Choose a document", 
            type=['docx', 'txt'], 
            help="Upload your research paper draft (Word or Text file)"
        )
        
        # Category selection
        selected_categories = st.sidebar.multiselect(
            "Select Research Categories", 
            self.categories,
            help="Choose the categories that best match your research paper"
        )
        
        # Process button
        process_button = st.sidebar.button("Generate References & Citations")
        
        # Main content area for display
        main_area = st.empty()
        
        if uploaded_file and process_button and selected_categories:
            try:
                # Save uploaded file temporarily
                temp_input_path = os.path.join("temp", f"input_{uploaded_file.name}")
                temp_output_path = os.path.join("temp", f"output_{uploaded_file.name}")
                
                # Ensure temp directory exists
                os.makedirs("temp", exist_ok=True)
                
                # Write uploaded file
                with open(temp_input_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Initialize keyword matcher and reference generator
                keyword_matcher = ExtractKeywords()
                reference_generator = ReferenceGenerator(style="APA")
                
                # Containers to display results
                with st.spinner("Processing your document..."):
                    # Lists to store results for each category
                    all_matching_papers = []
                    all_references = []
                    
                    # Process for each selected category
                    for category in selected_categories:
                        # Match keywords
                        matcher = PaperKeywordMatcher()
                        matching_titles = matcher.match_keywords(temp_input_path, category)

                        if matching_titles:
                            all_matching_papers.extend(matching_titles)

                            # Generate references for this category
                            references = reference_generator.generate_references(matching_titles, category)
                            all_references.extend(references)
                        
                        
                    
                    # Process in-text citations
                    if all_matching_papers:
                        # Choose first selected category for in-text citations
                        intext_citation = InTextCitationProcessor(
                            style="APA", 
                            collection_name=selected_categories[0]
                        )
                        modified_file_path = intext_citation.process_sentences(
                            temp_input_path, 
                            temp_output_path
                        )
                        
                        # Display results
                        st.success("Document processed successfully!")
                        
                        # Display matching papers
                        st.subheader("Matching Papers")
                        for paper in all_matching_papers:
                            st.write(f"- {paper}")
                        
                        # Display references
                        st.subheader("Generated References")
                        for ref in all_references:
                            st.write(f"- {ref}")
                        
                        # Download button for modified document
                        with open(modified_file_path, "rb") as file:
                            st.download_button(
                                label="Download Modified Document",
                                data=file.read(),
                                file_name=f"referenced_{uploaded_file.name}",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                            )
                    else:
                        st.warning("No matching papers found for the selected categories.")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")

def main():
    assistant = ResearchPaperAssistant()
    assistant.run()

if __name__ == "__main__":
    main()