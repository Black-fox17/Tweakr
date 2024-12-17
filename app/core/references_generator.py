import json
from datetime import datetime, date
from sqlalchemy.orm import Session
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers


class ReferenceGenerator:
    def __init__(self, style="APA"):
        self.style = style
        self.styles = {
            "APA": self.generate_apa_reference,
            "MLA": self.generate_mla_reference,
            "Chicago": self.generate_chicago_reference,
        }

    def format_author_list(self, authors: list, style: str) -> str:
        """
        Formats a list of authors based on the specified style.
        """
        if not authors:
            return ""
        if style == "APA":
            formatted_authors = [
                f"{author.split()[-1]}, {' '.join([name[0] + '.' for name in author.split()[:-1]])}"
                for author in authors
            ]
            if len(formatted_authors) > 1:
                return ", ".join(formatted_authors[:-1]) + f", & {formatted_authors[-1]}"
            return formatted_authors[0]
        elif style == "MLA":
            if len(authors) == 1:
                return authors[0]
            elif len(authors) == 2:
                return f"{authors[0]} and {authors[1]}"
            else:
                return f"{authors[0]} et al."
        elif style == "Chicago":
            return ", ".join(authors)
        return ", ".join(authors)

    def parse_authors(self, authors: str) -> list:
        """
        Parses the authors field from the database.
        Returns a list of authors.
        """
        if not authors:
            return []
        try:
            # Attempt to parse as JSON
            return json.loads(authors) if authors.startswith("[") else [author.strip() for author in authors.split(",")]
        except json.JSONDecodeError:
            # Fallback to treating as a comma-separated string
            return [author.strip() for author in authors.split(",")]

    def generate_apa_reference(self, paper, authors: list) -> str:
        """
        Generates an APA-style reference for a single paper.
        """
        title = paper.title.capitalize()
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."

        formatted_authors = self.format_author_list(authors, "APA")
        return f"""{formatted_authors} ({publication_year}). "{title}". {paper.category}."""

    def generate_mla_reference(self, paper, authors: list) -> str:
        """
        Generates an MLA-style reference for a single paper.
        """
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."

        formatted_authors = self.format_author_list(authors, "MLA")
        return f"""{formatted_authors}. "{title}." {paper.category}, {publication_year}."""


    def generate_chicago_reference(self, paper, authors: list) -> str:
        """
        Generates a Chicago-style reference for a single paper.
        """
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."

        formatted_authors = self.format_author_list(authors, "Chicago")
        return f"""{formatted_authors}. "{title}". {paper.category}, {publication_year}."""

    def generate_references(self, matching_titles: list, category: str) -> list:
        """
        Generates references for the matching papers based on the selected style.
        """
        references = []
        with get_session_with_ctx_manager() as session:
            for title in matching_titles:
                paper = session.query(Papers).filter(Papers.title == title, Papers.category == category).first()
                if paper:
                    # Fetch authors dynamically for each paper
                    authors = self.parse_authors(paper.authors)

                    # Generate references based on the selected style
                    reference_func = self.styles.get(self.style)
                    if reference_func:
                        references.append(reference_func(paper, authors))
                    else:
                        raise ValueError(f"Unsupported reference style: {self.style}")
        return references
