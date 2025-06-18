import { saveAs } from 'file-saver';
import { Document, Packer, Paragraph, TextRun, HeadingLevel, ExternalHyperlink, AlignmentType } from 'docx';

interface PaperDetails {
  authors?: string[];
  year?: string;
  title?: string;
  url?: string;
  doi?: string;
  [key: string]: any;
}

interface Citation {
  original_sentence?: string;
  paper_details?: PaperDetails;
  page_number?: string;
}

interface ProcessDocumentStyle {
  rawText: string;
  citations: Citation[];
  styleGuide: string;
}

export const processDocument = async ({ rawText, citations, styleGuide = 'APA' }: ProcessDocumentStyle): Promise<Blob> => {
  try {
    const annotatedText = annotateTextWithCitation(rawText, citations);
    const referencesChildren = formatReferences(citations, styleGuide);
    const doc = createWordDocument(annotatedText, referencesChildren);
    const blob = await Packer.toBlob(doc);
    return blob;
  } catch (error) {
    console.error('Error processing document:', error);
    throw new Error('Failed to process document');
  }
};

export const downloadDocument = (blob: Blob, filename = 'document_with_citations.docx') => {
  saveAs(blob, filename);
};

const annotateTextWithCitation = (text: string, citations: Citation[]): string => {
  if (!text || !citations || citations.length === 0) {
    return text;
  }

  let annotatedText = text;

  const sortedCitations = [...citations].sort((a, b) =>
    (b.original_sentence?.length || 0) - (a.original_sentence?.length || 0)
  );

  sortedCitations.forEach(citation => {
    if (!citation.original_sentence || !citation.paper_details) return;

    const { original_sentence } = citation;
    const { authors, year } = citation.paper_details;

    const authorLastName = (authors && Array.isArray(authors) && authors.length > 0 && typeof authors[0] === 'string')
      ? authors[0].split(' ').pop()
      : 'Unknown';

    const citationMarker = `(${authorLastName}, ${year || 'n.d.'})`;

    const escapedSentence = original_sentence
      .replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      .trim();

    const sentenceRegex = new RegExp(`${escapedSentence.replace(/\s+/g, '\\s+')}[.?!]?`, 'gi');

    annotatedText = annotatedText.replace(sentenceRegex, (match) => {
      const punctuationRegex = /[.?!]$/;
      let sentenceContent = match;
      let punctuation = '';

      const punctuationMatchResult = match.match(punctuationRegex);
      if (punctuationMatchResult) {
        punctuation = punctuationMatchResult[0];
        sentenceContent = match.substring(0, match.length - punctuation.length);
      }
      return `${sentenceContent.trimEnd()} ${citationMarker}${punctuation}`;
    });
  });

  return annotatedText;
};

const formatReferences = (citations: Citation[], styleGuide: string): (TextRun | ExternalHyperlink)[][] => {
  const uniquePapersData: { [key: string]: any } = {};

  citations.forEach(citation => {
    if (!citation.paper_details) return;
    const { doi, url, title } = citation.paper_details;
    const key = doi || url || title || JSON.stringify(citation.paper_details);
    const currentPageNumber = citation.page_number;
    if (!uniquePapersData[key]) {
      uniquePapersData[key] = {
        ...citation.paper_details,
        page_number: currentPageNumber
      };
    } else {
      if (!uniquePapersData[key].page_number && currentPageNumber) {
        uniquePapersData[key].page_number = currentPageNumber;
      }
    }
  });

  return Object.values(uniquePapersData).map(paperData => {
    const { authors, title, year, url, doi, page_number } = paperData as any;
    const authorText = (authors && Array.isArray(authors) && authors.length > 0) ? authors.join(', ') : 'Unknown Author';
    const yearText = year || 'n.d.';
    const titleText = title || 'Untitled';
    const pageText = page_number ? `p. ${page_number}` : '';
    const sourceLink = doi ? `https://doi.org/${doi}` : url;
    const children: (TextRun | ExternalHyperlink)[] = [];

    switch (styleGuide.toUpperCase()) {
      case 'APA':
        children.push(new TextRun(`${authorText} (${yearText}). `));
        children.push(new TextRun({ text: titleText, italics: true }));
        children.push(new TextRun("."));
        if (pageText) {
          children.push(new TextRun(` ${pageText}.`));
        }
        if (sourceLink) {
          children.push(new TextRun(" "));
          children.push(new ExternalHyperlink({
            children: [new TextRun({ text: sourceLink, style: "Hyperlink" })],
            link: sourceLink,
          }));
        }
        break;
      case 'MLA':
        children.push(new TextRun(`${authorText}. "${titleText}." ${yearText}`));
        if (pageText) {
          children.push(new TextRun(`, ${pageText}`));
        }
        children.push(new TextRun(`. Web. `));
        if (sourceLink) {
          children.push(new ExternalHyperlink({
            children: [new TextRun({ text: sourceLink, style: "Hyperlink" })],
            link: sourceLink,
          }));
        }
        break;
      case 'CHICAGO':
        let chicagoRefString = `${authorText}. "${titleText}." ${yearText}`;
        if (pageText) {
          chicagoRefString += `, ${pageText}`;
        }
        chicagoRefString += ".";
        children.push(new TextRun(chicagoRefString));
        if (sourceLink) {
          children.push(new TextRun(" "));
          children.push(new ExternalHyperlink({
            children: [new TextRun({ text: sourceLink, style: "Hyperlink" })],
            link: sourceLink,
          }));
          children.push(new TextRun("."));
        }
        break;
      default:
        children.push(new TextRun(`${authorText} (${yearText}). `));
        children.push(new TextRun({ text: titleText, italics: true }));
        children.push(new TextRun("."));
        if (pageText) {
          children.push(new TextRun(` ${pageText}.`));
        }
        if (sourceLink) {
          children.push(new TextRun(" "));
          children.push(new ExternalHyperlink({
            children: [new TextRun({ text: sourceLink, style: "Hyperlink" })],
            link: sourceLink,
          }));
        }
        break;
    }
    return children;
  });
};

const createWordDocument = (annotatedText: string, referencesChildren: (TextRun | ExternalHyperlink)[][]): Document => {
  const paragraphs = annotatedText.split('\n').filter(p => p.trim() !== '');
  const documentParagraphs = paragraphs.map(text =>
    new Paragraph({
      children: [new TextRun(text)],
      spacing: {
        after: 200,
        line: 360,
      },
    })
  );
  const referencesParagraphs = [
    new Paragraph({
      text: 'References',
      heading: HeadingLevel.HEADING_1,
      alignment: AlignmentType.CENTER,
      spacing: {
        before: 600,
        after: 300,
        line: 360,
      },
    }),
    ...referencesChildren.map(children =>
      new Paragraph({
        children,
        spacing: {
          after: 200,
          line: 360,
        },
        indent: {
          hanging: 720,
        },
      })
    ),
  ];
  return new Document({
    sections: [
      {
        properties: {},
        children: [...documentParagraphs, ...referencesParagraphs],
      },
    ],
  });
};

export const handleFinalize = async (
  extract: any,
  acceptedCitations: Citation[],
  styleGuide = 'APA'
): Promise<{
  documentUrl: string;
  downloadFile: () => void;
  statistics: { citationCount: number; referenceCount: number };
}> => {
  if (!extract?.data?.content || acceptedCitations.length === 0) {
    throw new Error("No content or citations to process");
  }

  try {
    const blob = await processDocument({
      rawText: extract.data.content,
      citations: acceptedCitations,
      styleGuide
    });
    const documentUrl = URL.createObjectURL(blob);
    return {
      documentUrl,
      downloadFile: () => downloadDocument(blob),
      statistics: {
        citationCount: acceptedCitations.length,
        referenceCount: getUniqueReferencesCount(acceptedCitations),
      }
    };
  } catch (error) {
    console.error('Failed to finalize document:', error);
    throw error;
  }
};

const getUniqueReferencesCount = (citations: Citation[]): number => {
  const uniquePapers = new Set<string>();
  citations.forEach(citation => {
    if (!citation.paper_details) return;
    const { doi, url, title } = citation.paper_details;
    const key = doi || url || title || '';
    uniquePapers.add(key);
  });
  return uniquePapers.size;
};