# app/core/hyperlink_helper.py 
import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def add_hyperlink(paragraph, url, text, color="0000FF", underline=True):
    """
    A function that places a hyperlink within a paragraph object.
    :param paragraph: The docx paragraph object.
    :param url: The URL for the hyperlink.
    :param text: The text to be displayed for the hyperlink.
    :param color: Hex color code as string (default blue).
    :param underline: Boolean indicating whether the text should be underlined.
    :return: The hyperlink element.
    """
    # Get the document part for relationship management.
    part = paragraph.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)

    # Create the hyperlink tag and set its relationship id.
    hyperlink = OxmlElement('w:hyperlink')
    hyperlink.set(qn('r:id'), r_id)

    # Create a run (<w:r>) and its properties (<w:rPr>).
    new_run = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')

    # Add color
    c = OxmlElement('w:color')
    c.set(qn('w:val'), color)
    rPr.append(c)

    # Underline
    if underline:
        u = OxmlElement('w:u')
        u.set(qn('w:val'), "single")
        rPr.append(u)

    new_run.append(rPr)
    # Create text element and add it to the run.
    text_elem = OxmlElement('w:t')
    text_elem.text = text
    new_run.append(text_elem)

    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)
    return hyperlink
