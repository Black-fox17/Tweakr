from enum import Enum, auto


class ContentType(Enum):
    """
    Enumerate different types of content a user can submit
    """

    LINK = "Link"
    PDF = "PDF Document"
    DOCX = "Word Document"
    TXT = "Text File"
    WEBPAGE = "Web Page"
    YOUTUBE_TRANSCRIPT = "YouTube Transcript"
    BOOK_CHAPTER = "Book Chapter"
    BOOK_PAGE = "Book Page"
