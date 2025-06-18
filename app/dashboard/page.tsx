"use client"

import Link from 'next/link'
import { motion } from 'framer-motion'
import React, { useEffect, useState, useMemo } from 'react'
import FileUploader from '../components/Fileuploader'
import CitattionCustomizationStation from '../components/CitattionCustomizationStation'
import {
    ChevronLeftIcon,
    ChevronRight,
    Clipboard,
    RotateCw,
    Settings,
    Zap,
    ArrowDown,
    X
} from 'lucide-react'
import CitationSuggestionBox, { Citation } from '../components/CitationSuggestionBox'
import CitationIsReadyModal from '../components/CitationIsReadyModal'
import CreateAccountModal from '../components/CreateAccountModal'
import CitationPerfectionAchieve from '../components/CitationPerfectionAchieve'
import { getCitationSuggestions, extractContent, charCount } from '@/service/citationService'
import { useQuery } from '@tanstack/react-query'
// import { verifySubscriptionPayment } from '@/service/subscriptionService'
import CostBreakDown from '../components/CostBreakDown'
import { annotateTextWithCitation } from '@/hooks/annotateTextWithCitations'
// import { handleFinalize as handleFinalizeFromProcessor } from '@/lib/documentProcessor'
import { toast } from 'sonner'
import CitationReferencesBox from '../components/CitationReferencesBox'

// Define a type for the result of the processor's handleFinalize
type DocumentProcessingResult = {
    documentUrl: string;
    downloadFile: () => void;
    statistics: {
        citationCount: number;
        referenceCount: number;
    };
} | null;

// Define the type for citation styles, mirroring what CitationSuggestionBox expects for its prop
type CitationStyle = 'APA' | 'MLA' | 'Chicago' | 'Harvard';

const Page = () => {
    const [uploadedFiles, setUploadedFiles] = useState<File[]>([])
    const [showAssistant, setShowAssistant] = useState(false)
    const [isSidebarOpen, setIsSidebarOpen] = useState(false)
    const [isCitationReady, setIsCitationReady] = useState(false)
    const [isRegisterReady, setIsRegisterReady] = useState(false)
    const [isCitationPerfectionAchieved, setIsCitationPerfectionAchieved] = useState(false)
    const [isLogin, setIsLogin] = useState(false)
    const [isPayment, setIsPayment] = useState(false)
    const [activeTab, setActiveTab] = useState<'suggestions' | 'settings' | 'references'>('settings')
    const [isUploading, setIsUploading] = useState(false);
    const [wordCount, setWordCount] = useState(0);
    const [annotatedText, setAnnotatedText] = useState('');
    const [token, setToken] = useState<string | null>(null);

    // New state variables for document processing
    const [selectedStyleGuide, setSelectedStyleGuide] = useState<CitationStyle>('APA');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [citationIntensity, setCitationIntensity] = useState('');
    const [acceptedCitations, setAcceptedCitations] = useState<Citation[]>([]);
    const [dismissedCitations, setDismissedCitations] = useState<Citation[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);

    // State to hold the result from documentProcessor.handleFinalize
    const [processingResult, setProcessingResult] = useState<DocumentProcessingResult>(null);

    // Check for token in localStorage only after component is mounted
    useEffect(() => {
        // Only access localStorage after the component has mounted
        const storedToken = typeof window !== 'undefined' ? localStorage.getItem("token") : null;
        setToken(storedToken);
    }, []);

    const formData = new FormData();
    if (uploadedFiles[0]) {
        formData.append('file', uploadedFiles[0]);
    }

    // useEffect(() => {
    //     const checkPayment = async () => {
    //         try {
    //             const response = await verifySubscriptionPayment(userId);
    //             console.log(response)
    //             const hasPaid = response?.data === true || response?.data?.status === true;

    //             if (hasPaid) {
    //                 setIsPaymentRequired(false);
    //             }
    //         } catch (error) {
    //             console.error('Payment verification failed:', error);
    //         }
    //     };

    //     checkPayment();
    // }, []);

    const createFormDataForFileUpload = (fieldName: string = 'file', collectionName: string = '') => {
        const formData = new FormData();
        if (uploadedFiles.length > 0 && uploadedFiles[0]) {
            formData.append(fieldName, uploadedFiles[0]);
        }
        if (collectionName) {
            formData.append('collection_name', collectionName);
        }
        return formData;
    };

    const { data: citationSuggestionsData, refetch: refetchSuggestions, isFetching: isLoadingSuggestions, error: suggestionsError, isSuccess: suggestionSuccesful } = useQuery({
        queryKey: ['getCitationSuggestions', selectedCategory],
        queryFn: async () => {
            const formData = createFormDataForFileUpload('input_file', selectedCategory);
            if (!formData.has('input_file')) {
                toast.error("Please upload a file first for suggestions.");
                return null;
            }
            return getCitationSuggestions(formData);
        },
        enabled: false,
    });

    if (suggestionsError) {
        console.error('Failed to get suggestions:', suggestionsError);
        toast.error("Failed to get suggestions. Please try again.");
    }

    const { data: extractResult, isSuccess: extractIsSuccess, isFetching: isLoadingExtract } = useQuery({
        queryKey: ['extract-content', uploadedFiles[0]?.name],
        queryFn: () => {
            // Check if file is PDF format
            const file = uploadedFiles[0];
            const isPDF = file.type === 'application/pdf' ||
                file.name.toLowerCase().endsWith('.pdf');

            if (isPDF) {
                toast.error("PDF format is not accepted. Please upload a different file format.");
                return Promise.reject(new Error("PDF format is not accepted"));
            }

            const formData = createFormDataForFileUpload('file');

            if (!formData.has('file')) {
                toast.error("Error: File not correctly added to form data for extraction.");
                return Promise.reject(new Error("File not found in form data for extraction"));
            } else {
                toast.success("File added to form data for extraction.");
            }

            return extractContent(formData);
        },
        enabled: uploadedFiles.length > 0 && !!uploadedFiles[0],
        refetchOnWindowFocus: false,
    });

    useEffect(() => {
        if (suggestionSuccesful && citationSuggestionsData) {
            setIsCitationReady(true);
        }
    }, [suggestionSuccesful, citationSuggestionsData]);

    useEffect(() => {
        // Check token after component has mounted
        if (typeof window !== 'undefined') {
            const storedToken = localStorage.getItem('token');
            if (storedToken) {
                setIsRegisterReady(false);
            }
        }
    }, []);

    // This timeout keeps CitationReady for 10s, then clears it
    useEffect(() => {
        if (isCitationReady) {
            const timeout = setTimeout(() => {
                setIsCitationReady(false);
                // Once citation ends, optionally set registration
                setIsRegisterReady(true);
            }, 10000);

            return () => clearTimeout(timeout);
        }
    }, [isCitationReady]);

    useEffect(() => {
        if (extractIsSuccess && extractResult) {
            const text = typeof extractResult.data?.content === "string" ? extractResult.data.content : "";
            setAnnotatedText(text);
            const words = text.trim().split(/\s+/);
            setWordCount(words.length);
            setIsUploading(false);
        }
    }, [extractIsSuccess, extractResult]);

    const file = uploadedFiles[0];

    const { data: charCountData, isSuccess: suucessCharCount } = useQuery({
        queryKey: ['char-count', file?.name],
        queryFn: () => charCount(formData),
        enabled: !!file && !!formData,
        refetchOnWindowFocus: false,
    });

    useEffect(() => {
        if (suucessCharCount) {
            setWordCount(charCountData?.data?.word_count);
        }
    }, [suucessCharCount, charCountData, file?.name]);

    useEffect(() => {
        if (uploadedFiles.length > 0) {
            setIsUploading(true);
        }
    }, [uploadedFiles]);

    const handleWorkMagic = () => {
        if (!uploadedFiles[0]) {
            toast.error("Please upload a document first.");
            return;
        }
        if (!selectedCategory || selectedCategory.trim() === '') {
            toast.error('Please select a category before proceeding!');
            return;
        }

        // Check if style guide is selected
        if (!selectedStyleGuide) {
            toast.error('Please select a style guide!');
            return;
        }

        refetchSuggestions();
        setActiveTab("suggestions");
    };

    const suggestionsToDisplay = useMemo(() => {
        return citationSuggestionsData?.data?.citations?.flat().filter((citation: Citation) =>
            !acceptedCitations.find(c => c.id === citation.id) &&
            !dismissedCitations.find(c => c.id === citation.id)
        ) || [];
    }, [citationSuggestionsData, acceptedCitations, dismissedCitations]);

    const handleAcceptAll = () => {
        if (!citationSuggestionsData?.data?.citations) return;
        const flatCitations: Citation[] = citationSuggestionsData.data.citations.flat();

        const newAccepted = flatCitations.filter((citation: Citation) =>
            !acceptedCitations.find(c => c.id === citation.id) &&
            !dismissedCitations.find(c => c.id === citation.id)
        );

        const updatedAcceptedCitations = [...acceptedCitations, ...newAccepted];
        setAcceptedCitations(updatedAcceptedCitations);

        if (extractResult?.data?.content) {
            const rawText = extractResult.data.content;
            const updatedLiveText = annotateTextWithCitation(rawText, updatedAcceptedCitations);
            setAnnotatedText(updatedLiveText);
        }

        setIsSidebarOpen(false)
        setShowAssistant(false)
    };

    const handleAcceptCitation = (citation: Citation) => {
        setAcceptedCitations(prev => {
            const alreadyAccepted = prev.some(c => c.id === citation.id);
            if (alreadyAccepted) return prev;

            const updated = [...prev, citation];
            if (extractResult?.data?.content) {
                const rawText = extractResult.data.content;
                const updatedLiveText = annotateTextWithCitation(rawText, updated);
                setAnnotatedText(updatedLiveText);
            }
            return updated;
        });
    };

    const handleDismissCitation = (citation: Citation) => {
        setDismissedCitations(prev => [...prev, citation]);
        setAcceptedCitations(prev => prev.filter(c => c.id !== citation.id));
    };

    const handleFinalizeDocument = () => {
        if (!acceptedCitations || acceptedCitations.length < 1) {
            toast.error("Accept citation before finalizing")
            return
        }
        setIsPayment(true);
    }

    const handleCompleteCitationTransportation = async (citationsFromBox: Citation[]) => {
        if (!extractResult?.data?.content || citationsFromBox.length === 0) {
            toast.error("No content or citations to process.");
            setProcessingResult(null);
            setIsCitationPerfectionAchieved(false);
            return;
        }

        setIsProcessing(true);
        setProcessingResult(null);
        setIsCitationPerfectionAchieved(false);

        try {
            const result = await handleFinalizeFromProcessor(
                extractResult,
                citationsFromBox,
                selectedStyleGuide
            );
            setProcessingResult(result);
            setIsCitationPerfectionAchieved(true);
        } catch (error) {
            console.error('Error finalizing document:', error);
            toast.error(error instanceof Error ? error.message : 'Failed to finalize document.');
            setIsCitationPerfectionAchieved(false);
        } finally {
            setIsProcessing(false);
        }
    };

    return (
        <>
            {isCitationReady && <CitationIsReadyModal />}
            {isRegisterReady && !token &&
                <CreateAccountModal
                    isLogin={isLogin}
                    setIsLogin={setIsLogin}
                    setIsRegisterReady={setIsRegisterReady} />
            }

            {isCitationPerfectionAchieved && processingResult && !isProcessing && (
                <CitationPerfectionAchieve
                    // documentUrl={processingResult.documentUrl}
                    onDownloadClick={processingResult.downloadFile}
                    citationCount={processingResult.statistics.citationCount}
                    referenceCount={processingResult.statistics.referenceCount}
                    setIsCitationPerfectionAchieved={setIsCitationPerfectionAchieved}
                />
            )}

            <div className="relative flex h-screen w-full bg-white transition-all duration-500">
                <div
                    className={`flex flex-1 flex-col transition-all duration-500 ${showAssistant && isSidebarOpen ? 'w-[70%]' : 'w-full'
                        }`}
                >
                    {/* main nav */}
                    <nav
                        className={`${isSidebarOpen ? "py-3" : "py-6 sm:px-12"} relative flex h-16 w-full items-center justify-between border-b border-[#EDEDED] bg-white pl-2 sm:pl-12 `}
                    >
                        <Link href="/">
                            <img src="/assets/Green (2).svg" alt="logo" />
                        </Link>
                        <div className="left-[40%] hidden max-w-80 truncate rounded-[8px] bg-[#EAFBF9] px-2 py-1 text-[20px] font-medium text-[#545454] sm:block">
                            {uploadedFiles[0]?.name || "Untitled Document"}
                        </div>
                        <div className='fixed right-2 flex gap-2 sm:hidden'>
                            <div className='flex gap-2 sm:hidden'>
                                <div className="rounded-[8px] bg-[#EAFBF9] px-2 py-1 text-[20px] font-medium text-[#545454]">
                                    <p className='max-w-32 truncate'>
                                        {file ? file?.name : "Untitled Document"}
                                    </p>
                                </div>
                                <div>
                                    <button
                                        className='items-center rounded-full border-[1.75px] border-[#616161] p-2.5  shadow-sm'
                                        onClick={() => {
                                            setIsSidebarOpen((prev) => !prev)
                                            setShowAssistant((prev) => !prev)
                                        }}
                                    >
                                        <ArrowDown className='size-4' />
                                    </button>
                                    {/* Pointer animation */}
                                    {!showAssistant && !isSidebarOpen && extractIsSuccess && (
                                        <div className="right-1/8 absolute top-16 z-10 -translate-x-1/2 animate-bounce text-[24px]">
                                            👆
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                        <div className="relative w-fit">
                            {/* The target button */}
                            {!showAssistant && !isSidebarOpen && extractIsSuccess && (
                                <div className="absolute left-4 top-8 z-10 -translate-x-1/2 animate-bounce text-[24px] sm:left-1/2 sm:top-16">
                                    👆
                                </div>
                            )}
                            {!showAssistant && !isSidebarOpen ? (
                                <button
                                    className="hidden animate-pulse rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-medium text-white sm:flex"
                                    onClick={() => {
                                        setIsSidebarOpen((prev) => !prev)
                                        setShowAssistant((prev) => !prev)
                                    }}
                                >
                                    Check Assistants
                                </button>
                            ) : (
                                <div className="hidden items-center gap-4 sm:flex">
                                    <button
                                        onClick={() => {
                                            setUploadedFiles([])
                                            setActiveTab('settings')
                                            setIsPayment(false)
                                        }}
                                        className="flex items-center gap-2 rounded-full border-[1.75px] border-[#616161] bg-[#FAFAFA] p-4 text-[12px] shadow-sm"
                                    >
                                        <RotateCw className="size-[16px]" />
                                        Reupload
                                    </button>
                                    <button
                                        className="rounded-l-[4px] border border-[#EDEDED] p-[10px]"
                                        onClick={() => {
                                            setIsSidebarOpen((prev) => !prev)
                                            setShowAssistant((prev) => !prev)
                                        }}
                                    >
                                        {isSidebarOpen ? (
                                            <ChevronRight className="size-[24px]" />
                                        ) : (
                                            <ChevronLeftIcon className="size-[24px]" />
                                        )}
                                    </button>
                                </div>
                            )}
                        </div>
                    </nav>

                    {/* main view */}
                    <div className="scrollbar-hide flex w-full flex-1 flex-col items-center justify-center overflow-y-auto px-4 py-6  sm:px-12">
                        {isLoadingExtract && !extractResult && (
                            <div className="scrollbar-hide w-full  space-y-4">
                                {Array.from({ length: 40 }).map((_, index) => (
                                    <div key={index} className="h-[22px] w-full animate-pulse rounded bg-[#D9D9D9]" />
                                ))}
                            </div>
                        )}
                        {!isLoadingExtract && !extractIsSuccess && !isLoadingSuggestions && !uploadedFiles.length ? (
                            <FileUploader
                                files={uploadedFiles}
                                onChange={(files) => setUploadedFiles(files as File[])}
                                isPending={isUploading}
                            />
                        ) : isLoadingSuggestions && !citationSuggestionsData ? (
                            <div className="r-hide w-full  space-y-4">
                                {Array.from({ length: 40 }).map((_, index) => (
                                    <div key={index} className="h-[22px] w-full animate-pulse rounded bg-[#D9D9D9]" />
                                ))}
                            </div>
                        ) : isCitationPerfectionAchieved && processingResult ? (
                            <div className="w-full overflow-y-scroll py-4 text-center">
                                <h2 className="mb-4 text-2xl font-semibold">Document Ready!</h2>
                                <p className="mb-2 text-lg">Your document{uploadedFiles[0]?.name} has been processed.</p>
                                <p className="text-md mb-1">Citations: {processingResult.statistics.citationCount}</p>
                                <p className="text-md mb-4">References: {processingResult.statistics.referenceCount}</p>
                            </div>
                        ) : extractResult?.data?.content ? (
                            <div className="scrollbar-hide w-full  overflow-y-scroll py-4">
                                <p className="whitespace-pre-wrap text-[#545454]">
                                    {annotatedText}
                                </p>
                            </div>
                        ) : (
                            <div className="text-center">
                                {uploadedFiles.length > 0 && !extractResult && !isLoadingExtract && (
                                    <p className="text-red-500">Could not extract content from the uploaded file.
                                        <br />
                                        Reload Page to upload valid file format
                                    </p>
                                )}
                            </div>
                        )}
                    </div>
                </div >

                {/* sidebar  */}
                {showAssistant && (
                    <motion.div
                        initial={{ opacity: 0, y: "100%" }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: "100%" }}
                        transition={{ duration: 0.4, ease: "easeInOut" }}
                        className={`transition-transform duration-500 ease-in-out${isSidebarOpen ? ' translate-y-0' : 'translate-y-full'} lg:${isSidebarOpen ? 'translate-x-0' : 'translate-x-full'}   fixed right-0 top-0 z-0  size-full overflow-hidden  border border-[#EDEDED] bg-[#FDFDFD] sm:z-30 sm:mt-0  lg:static lg:w-[38%] `}
                    >
                        <div className="flex size-full flex-col ">
                            <div className='max-w-full'>
                                <nav
                                    className={`${isSidebarOpen ? "py-3" : "py-6 sm:px-12"} relative flex h-16 w-full items-center justify-between border-b border-[#EDEDED] bg-white px-2 lg:hidden `}
                                >
                                    <Link href="/">
                                        <img src="/assets/Green (2).svg" alt="logo" />
                                    </Link>
                                    <div className='flex items-center gap-2 sm:hidden'>
                                        <div className="rounded-[8px] bg-[#EAFBF9] px-2 py-1 text-[20px] font-medium text-[#545454]">
                                            <p className='max-w-32 truncate'>
                                                {file ? file?.name : "Untitled Document"}
                                            </p>
                                        </div>
                                        <button
                                            className='items-center rounded-full border-[1.75px] border-[#616161] p-2.5  shadow-sm'
                                            onClick={() => {
                                                setIsSidebarOpen((prev) => !prev)
                                                setShowAssistant((prev) => !prev)
                                            }}
                                        >
                                            <X className="size-4" />
                                        </button>
                                    </div>
                                </nav>
                            </div>
                            <nav className="scrollbar-hide hidden h-16 items-center justify-between overflow-x-scroll border-b border-b-[#EDEDED] bg-white p-4 lg:flex">
                                <button
                                    className={`${activeTab === 'settings' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex w-[144px] items-center justify-start gap-2 rounded-[8px] px-4 py-2 transition-all duration-300`}
                                    onClick={() => setActiveTab('settings')}
                                >
                                    <Settings />
                                    Settings
                                </button>
                                <button
                                    className={` ${activeTab === 'suggestions' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex items-center justify-start gap-2 rounded-[8px] px-4 py-2 transition-all duration-300`}
                                    onClick={() => setActiveTab('suggestions')}
                                    disabled={!extractIsSuccess}
                                >
                                    <Zap />
                                    Suggestions
                                </button>
                                <button
                                    className={`${activeTab === 'references' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex items-center justify-start gap-2 rounded-[8px] px-4 py-2 transition-all duration-300`}
                                    onClick={() => setActiveTab('references')}
                                    disabled={!extractIsSuccess}
                                >
                                    <Clipboard className='size-[16px]' />
                                    References
                                </button>
                            </nav>

                            <div className="relative flex-1 overflow-y-auto">
                                {activeTab === 'suggestions' && !isPayment && (
                                    <CitationSuggestionBox
                                        suggestions={suggestionsToDisplay}
                                        onAccept={handleAcceptCitation}
                                        onDismiss={handleDismissCitation}
                                        acceptedCitations={acceptedCitations}
                                        onAcceptAll={handleAcceptAll}
                                        onFinalize={handleFinalizeDocument}
                                        citationStyle={selectedStyleGuide}
                                        isProcessing={isLoadingSuggestions || isLoadingExtract}
                                    />
                                )}
                                {activeTab === 'settings' && !isPayment && (
                                    <CitattionCustomizationStation
                                        selectedStyleGuide={selectedStyleGuide}
                                        setSelectedStyleGuide={setSelectedStyleGuide}
                                        selectedCategory={selectedCategory}
                                        setSelectedCategory={setSelectedCategory}
                                        citationIntensity={citationIntensity}
                                        setCitationIntensity={setCitationIntensity}
                                        uploadedFile={uploadedFiles[0] || null} onWorkMagic={handleWorkMagic}
                                        isProcessing={isLoadingSuggestions || isLoadingExtract}
                                    />
                                )}
                                {activeTab === 'references' && !isPayment && <CitationReferencesBox />}
                                {activeTab === 'references' && !isPayment && processingResult && (
                                    <div className="p-4">
                                        <h3 className="mb-2 text-xl font-semibold">Document Statistics</h3>
                                        <p>Citations Added: {processingResult.statistics.citationCount}</p>
                                        <p>Reference Entries: {processingResult.statistics.referenceCount}</p>
                                    </div>
                                )}
                                {isPayment &&
                                    <CostBreakDown
                                        wordCount={wordCount}
                                        acceptedCitation={acceptedCitations.length}
                                        handleCompleteCitationTransportation={() =>
                                            handleCompleteCitationTransportation(acceptedCitations)
                                        }
                                        setIsCitationPerfectionAchieved={setIsCitationPerfectionAchieved}
                                    />
                                }

                            </div>
                        </div>
                    </motion.div>
                )
                }

                {/* mobile sidebar */}
                {showAssistant && isSidebarOpen && (
                    <div className='fixed bottom-0 left-0 z-40 flex w-full flex-col lg:hidden'>
                        {activeTab === 'suggestions' && !isPayment && !isLoadingSuggestions &&
                            (<div className='flex w-full items-center justify-between gap-3 bg-[#EDEDED] px-4 py-2'>
                                <button
                                    onClick={handleAcceptAll}
                                    className='w-full whitespace-nowrap rounded-sm border-[1.75px] border-[#545454] bg-white px-4 py-2 text-[14px] font-medium text-[#010F34] shadow-md'
                                >
                                    Accept All
                                </button>
                                <button
                                    onClick={handleFinalizeDocument}
                                    className='w-full rounded-sm bg-[#31DAC0] px-4 py-2 text-[14px] font-medium text-[#010F34] shadow-md'>
                                    Finalize
                                </button>
                            </div>)}
                        <nav className="flex w-full  items-center justify-around border-t border-t-[#EDEDED] bg-white px-4 py-2">
                            <button
                                className={`${activeTab === 'settings' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex w-1/3 flex-col items-center justify-center gap-1 rounded-[8px] px-3 py-2 text-xs transition-all duration-300`}
                                onClick={() => setActiveTab('settings')}
                            >
                                <Settings className='size-[20px]' />
                                Settings
                            </button>
                            <button
                                className={` ${activeTab === 'suggestions' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex w-1/3 flex-col items-center justify-center gap-1 rounded-[8px] px-3 py-2 text-xs transition-all duration-300`}
                                onClick={() => setActiveTab('suggestions')}
                                disabled={!extractIsSuccess}
                            >
                                <Zap className='size-[20px]' />
                                Suggestions
                            </button>
                            <button
                                className={`${activeTab === 'references' ? 'bg-[#E6E7EB] text-[#010F34]' : 'text-[#8A91A2]'} flex w-1/3 flex-col items-center justify-center gap-1 rounded-[8px] px-3 py-2 text-xs transition-all duration-300`}
                                onClick={() => setActiveTab('references')}
                                disabled={!extractIsSuccess}
                            >
                                <Clipboard className='size-[20px]' />
                                References
                            </button>
                        </nav>
                    </div>
                )
                }
            </div >
        </>
    )
}

export default Page