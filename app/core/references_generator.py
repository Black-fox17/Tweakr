# app/core/references_generator.py
import json
from datetime import datetime, date

class ReferenceGenerator:
    def __init__(self, style="APA"):
        self.style = style
        self.styles = {
            "APA": self.generate_apa_reference,
            "MLA": self.generate_mla_reference,
            "Chicago": self.generate_chicago_reference,
        }

    def format_author_list(self, authors: list, style: str) -> str:
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
        reference_text = f"{formatted_authors} ({publication_year}). \"{title}\"."
        # If a URL exists, return it (otherwise an empty string)
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url

    def generate_mla_reference(self, paper, authors: list) -> tuple:
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."
        formatted_authors = self.format_author_list(authors, "MLA")
        reference_text = f"{formatted_authors}. \"{title}.\", {publication_year}."
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url

    def generate_chicago_reference(self, paper, authors: list) -> tuple:
        title = paper.title
        pub_date = paper.pub_date
        publication_year = pub_date.year if isinstance(pub_date, (datetime, date)) else "n.d."
        formatted_authors = self.format_author_list(authors, "Chicago")
        reference_text = f"{formatted_authors}. \"{title}\"., {publication_year}."
        url = paper.url if hasattr(paper, "url") and paper.url else ""
        return reference_text, url

    def generate_references(self, matching_titles: list, category: str) -> list:
        references = []
        from datapipeline.core.database import get_session_with_ctx_manager
        from datapipeline.models.papers import Papers
        with get_session_with_ctx_manager() as session:
            for title in matching_titles:
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
