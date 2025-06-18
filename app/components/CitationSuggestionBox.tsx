import React, { useState } from 'react';
import { toast } from 'sonner';

export type Citation = {
    id: string;
    metadata: {
        paragraph_index: number;
        sentence_index: number;
    };
    original_sentence: string;
    paper_details: {
        title: string;
        authors: string[];
        year: string;
        url: string;
        doi: string;
    };
    status: string;
    page_number?: string;
};

type CitationSuggestionBoxProps = {
    suggestions: Citation[] | undefined;
    acceptedCitations?: Citation[];
    onAccept?: (citation: Citation) => void;
    onDismiss?: (citation: Citation) => void;
    onAcceptAll?: () => void;
    onFinalize?: (citationsToFinalize: Citation[]) => void;
    citationStyle?: 'APA' | 'MLA' | 'Chicago' | 'Harvard';
    isProcessing?: boolean;
};

const CitationSuggestionBox: React.FC<CitationSuggestionBoxProps> = ({
    suggestions,
    acceptedCitations = [],
    onAccept = () => { },
    onDismiss = () => { },
    onFinalize = () => { },
    onAcceptAll = () => { },
    citationStyle = 'APA',
    isProcessing,
}) => {
    // State to store generated references
    const [references, setReferences] = useState<string[]>([]);
    const [showReferences, setShowReferences] = useState<boolean>(false);
    const [isGeneratingReferences, setIsGeneratingReferences] = useState<boolean>(false);

    // Function to generate references
    const handleGenerateReferences = () => {
        if (acceptedCitations.length === 0) {
            alert("No citations have been accepted yet.");
            return;
        }

        setIsGeneratingReferences(true);

        // Update all accepted citations to have status "accepted"
        const citationsToSend = acceptedCitations.map(citation => ({
            ...citation,
            status: "accepted"
        }));

        // Send to backend API
        fetch('https://tweakr.onrender.com/api/v1/citations/update-citations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                citations: citationsToSend,
                style: citationStyle
            }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to generate references');
                }
                return response.json();
            })
            .then(data => {
                if (data.references && Array.isArray(data.references)) {
                    setReferences(data.references);
                    setShowReferences(true);
                } else {
                    console.error('Invalid references format received:', data);
                    alert('Failed to generate references. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error generating references:', error);
                alert('Failed to generate references. Please try again.');
            })
            .finally(() => {
                setIsGeneratingReferences(false);
            });
    };

    // Function to copy references to clipboard
    const copyReferencesToClipboard = () => {
        const referencesText = references.join('\n\n');
        navigator.clipboard.writeText(referencesText)
            .then(() => alert('References copied to clipboard!'))
            .catch(err => console.error('Failed to copy references: ', err));
    };

    // Function to handle accepting a citation - just call the parent handler
    const handleAccept = (citation: Citation) => {
        // Create updated citation with status set to "accepted"
        const updatedCitation = { ...citation, status: "accepted" };

        // Call the parent component's onAccept handler which will update the parent state
        onAccept(updatedCitation);
    };

    // Function to handle dismissing a citation
    const handleDismiss = (citation: Citation) => {
        // Call the parent component's onDismiss handler
        onDismiss(citation);
    };

    // Function to handle accepting all citations
    const handleAcceptAll = () => {
        if (!suggestions) return;
        const updatedCitations = suggestions.map(citation => ({
            ...citation,
            status: "accepted"
        }));

        onAcceptAll();
    };

    const handleFinalizeInternal = async () => {
        if (!acceptedCitations) {
            toast.error("Add citation before finalizing all process")
            return
        }
        if (onFinalize) {
            onFinalize(acceptedCitations);
        }
    };



    return (
        <div className="relative mx-auto mb-8 flex w-full max-w-3xl flex-col gap-[26px] p-0 sm:p-6 ">
            {suggestions && !isProcessing ? (
                <div className="relative flex w-full flex-col gap-4 p-4 sm:p-0">
                    {suggestions.map((suggestion, index) => {
                        const isAccepted = acceptedCitations.some(c => c.id === suggestion.id);
                        return (
                            <div key={suggestion.id || index} className="flex flex-col items-start gap-4 border-b p-2 text-[#545454] sm:p-4">
                                <p className='max-w-full truncate text-[20px]'><s>{suggestion.original_sentence}</s></p>
                                <p className='max-w-full truncate text-[20px] text-[#010F34]'>{suggestion.original_sentence}</p>
                                <p className='max-w-full truncate rounded-md bg-[#EAFBF9] p-2 text-[14px] font-medium text-[#010F34]'>
                                    Source: {suggestion.paper_details.title} ({suggestion.paper_details.year}) - {suggestion.paper_details.url}
                                </p>
                                <div className='flex gap-4'>
                                    <button
                                        className={`rounded-sm border-[1.75px] border-[#545454] px-4 py-3 text-[14px] font-medium text-[#010F34] shadow-md ${isAccepted ? 'bg-[#31DAC0]' : ''}`}
                                        onClick={() => handleAccept(suggestion)}
                                        disabled={isAccepted}
                                    >
                                        {isAccepted ? 'Accepted' : 'Accept'}
                                    </button>
                                    <button
                                        className='px-4 py-3 text-[14px] font-medium text-[#8A8A8A]'
                                        onClick={() => handleDismiss(suggestion)}
                                    >
                                        Dismiss
                                    </button>
                                </div>
                            </div>
                        )
                    })}

                    <div className='sticky bottom-0 mx-auto flex w-full items-center justify-between gap-3 bg-[#EDEDED] px-4 py-2'>
                        <button
                            onClick={handleAcceptAll}
                            className='w-full whitespace-nowrap rounded-sm border-[1.75px] border-[#545454] bg-white px-4 py-2 text-[14px] font-medium text-[#010F34] shadow-md'
                        >
                            Accept All
                        </button>
                        <button
                            onClick={handleFinalizeInternal}
                            className='w-full rounded-sm bg-[#31DAC0] px-4 py-2 text-[14px] font-medium text-[#010F34] shadow-md'>
                            Finalize
                        </button>
                    </div>
                </div>
            ) : (
                <div className='mb-40 flex h-full flex-col items-center justify-center gap-2'>
                    <img src="/gif/Docs animation gif.gif" alt="aniamtion" className=' object-contain' />
                    <h3 className="text-[20px] font-semibold text-[#010F34]">Citation in progress</h3>
                    <p className="text-[14px] font-medium text-[#010F34]">Suggestions will appear here in 3-minutes</p>
                </div>
            )}
        </div>
    );
};

export default CitationSuggestionBox;