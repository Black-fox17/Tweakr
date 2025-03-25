# app/core/references_generator.py
import json
from datetime import datetime, date
import random
from sqlalchemy import or_

class ReferenceGenerator:
    def __init__(self, style="APA"):
        self.style = style
        self.styles = {
            "APA": self.generate_apa_reference,
            "MLA": self.generate_mla_reference,
            "Chicago": self.generate_chicago_reference,
        }

    def format_author_list(self, authors: list, style: str) -> str:
        """Format author list using full names (not abbreviated) for the bibliography/references section."""
        if not authors:
            return ""
            
        if style == "APA":
            # Use full names, last name first for first author, then initials for first names
            formatted_authors = []
            for author in authors:
                names = author.split()
                if len(names) > 1:
                    # Last name first, then full first name(s)
                    formatted = f"{names[-1]}, {' '.join(names[:-1])}"
                else:
                    formatted = author
                formatted_authors.append(formatted)
                
            if len(formatted_authors) > 1:
                return ", ".join(formatted_authors[:-1]) + f", & {formatted_authors[-1]}"
            return formatted_authors[0]
            
        elif style == "MLA":
            # Full names, first author with last name first
            if len(authors) == 1:
                names = authors[0].split()
                if len(names) > 1:
                    return f"{names[-1]}, {' '.join(names[:-1])}"
                return authors[0]
            elif len(authors) == 2:
                names1 = authors[0].split()
                if len(names1) > 1:
                    first_author = f"{names1[-1]}, {' '.join(names1[:-1])}"
                else:
                    first_author = authors[0]
                return f"{first_author}, and {authors[1]}"
            else:
                names1 = authors[0].split()
                if len(names1) > 1:
                    first_author = f"{names1[-1]}, {' '.join(names1[:-1])}"
                else:
                    first_author = authors[0]
                return f"{first_author}, et al."
                
        elif style == "Chicago":
            # Full names in normal order
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]} and {authors[1]}"
            else:
                return f"{authors[0]} et al."
                
        # Default - just join with commas
        return ", ".join(authors)

    def parse_authors(self, authors: str) -> list:
        if not authors:
            return []
        if authors.startswith("[") and authors.endswith("]"):
            try:
                return json.loads(authors)
            except json.JSONDecodeError:
                pass
        return [author.strip() for author in authors.split(",")]

    def generate_apa_reference(self, paper, authors: list) -> tuple:
        title = paper.title.capitalize()
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."
        formatted_authors = self.format_author_list(authors, "APA")
        
        paper_num = random.randint(350, 1000)
        if hasattr(paper, "id") and paper.id:
            try:
                paper_id = int(paper.id)
                pages = f", {paper_id} - {paper_num}" if paper_id < paper_num else f", {paper_num} - {paper_id}"
            except ValueError:
                pages = ""  # Handle invalid paper.id gracefully
        else:
            pages = ""
        
        reference_text = f"{formatted_authors} ({publication_year}). \"{title}\"{pages}."
        # If a URL exists, return it (otherwise an empty string)
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url

    def generate_mla_reference(self, paper, authors: list) -> tuple:
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."
        formatted_authors = self.format_author_list(authors, "MLA")
        
        # Add page numbers if available
        pages = ""
        if hasattr(paper, "pages") and paper.pages:
            pages = f", pp. {paper.pages}"
        
        reference_text = f"{formatted_authors}. \"{title}.\"{pages}, {publication_year}."
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url

    def generate_chicago_reference(self, paper, authors: list) -> tuple:
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."
        formatted_authors = self.format_author_list(authors, "Chicago")
        
        # Add page numbers if available
        pages = ""
        if hasattr(paper, "pages") and paper.pages:
            pages = f", {paper.pages}"
        
        reference_text = f"{formatted_authors}. \"{title}\"{pages}. {publication_year}."
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url



    def generate_references(self, matching_titles: list, category: str) -> list:
        references = []
        from datapipeline.core.database import get_session_with_ctx_manager
        from datapipeline.models.papers import Papers

        with get_session_with_ctx_manager() as session:
            for title in matching_titles:
                # Adjust filter for corporate_governance to include governance
                if category == "corporate_governance":
                    paper = (
                        session.query(Papers)
                        .filter(
                            Papers.title == title,
                            or_(Papers.category == "corporate_governance", Papers.category == "governance")
                        )
                        .first()
                    )
                else:
                    paper = (
                        session.query(Papers)
                        .filter(Papers.title == title, Papers.category == category)
                        .first()
                    )

                if paper:
                    authors = self.parse_authors(paper.authors)
                    reference_func = self.styles.get(self.style)
                    if reference_func:
                        # Each reference is now a tuple: (reference_text, url)
                        references.append(reference_func(paper, authors))
                    else:
                        raise ValueError(f"Unsupported reference style: {self.style}")

        return references
