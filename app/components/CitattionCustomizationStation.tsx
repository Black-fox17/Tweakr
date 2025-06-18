'use client';

import { useQuery } from '@tanstack/react-query';
import { getCategories, getCategory } from '@/service/citationService';

import React from 'react';
import {
    Select,
    SelectContent,
    SelectGroup,
    SelectItem,
    SelectTrigger,
    SelectValue
} from '@/components/ui/select';


type CitationStyleType = 'APA' | 'MLA' | 'Chicago' | 'Harvard';

interface Props {
    selectedStyleGuide: CitationStyleType;
    setSelectedStyleGuide: (value: CitationStyleType) => void;
    selectedCategory: string;
    setSelectedCategory: (value: string) => void;
    citationIntensity: string;
    setCitationIntensity: (value: string) => void;
    onWorkMagic: () => void;
    isProcessing?: boolean;
    uploadedFile: File | null;
}

const CitationCustomizationStation = ({
    selectedStyleGuide,
    setSelectedStyleGuide,
    selectedCategory,
    setSelectedCategory,
    // citationIntensity,
    setCitationIntensity,
    onWorkMagic,
    // isProcessing,
    uploadedFile,
}: Props) => {

    const { data: category, isLoading } = useQuery({
        queryKey: ['categories', uploadedFile],
        queryFn: () => getCategory(uploadedFile as File),
        enabled: !!uploadedFile,
    });

    const { data: categories } = useQuery({
        queryKey: ['categories'],
        queryFn: () => getCategories(),
    });




    return (
        <div className="mx-auto mb-10 flex w-full max-w-3xl flex-col gap-[26px] p-6 sm:mb-0">
            <h3 className="text-[24px] font-semibold text-[#010F34]">Citation Customization Station</h3>
            <div className="h-[0.5px] w-full bg-[#D8D8D8]"></div>

            {/* Style Guide */}
            <div className="flex flex-col gap-2">
                <label className="text-[18px] font-semibold text-[#212121]">Which Style Guide Is Bossing You Around?</label>
                <Select value={selectedStyleGuide} onValueChange={(value) => setSelectedStyleGuide(value as CitationStyleType)}>
                    <SelectTrigger className="rounded-[10px] border-[#FAFAFA] p-4 text-[18px] text-[#9E9E9E]">
                        <SelectValue placeholder="Choose style guide..." />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            {["APA", "MLA", "Chicago", "Harvard"].map((value) => (
                                <SelectItem key={value} value={value}>{value}</SelectItem>
                            ))}
                        </SelectGroup>
                    </SelectContent>
                </Select>
            </div>

            {/* Timeframe */}
            <div className="flex flex-col gap-2">
                <label className="text-[18px] font-semibold text-[#212121]">Category</label>
                <Select value={selectedCategory} onValueChange={(value) => setSelectedCategory(value)}>
                    <SelectTrigger className="rounded-[10px] border-[#FAFAFA] p-4 text-[18px] text-[#9E9E9E]">
                        <SelectValue placeholder="Choose category..." />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectGroup>
                            {isLoading ? (
                                <div className="p-4 text-center text-gray-400">Loading...</div>
                            ) : (
                                <>
                                    <SelectItem value={category?.data?.category} >
                                        {category?.data?.category}
                                    </SelectItem>
                                    {/* All other categories, excluding the default if already shown */}
                                    {categories?.data?.categories
                                        ?.map((cat: string, index: number) => (
                                            <SelectItem key={index} value={cat}>
                                                {cat}
                                            </SelectItem>
                                        ))}
                                </>
                            )}
                        </SelectGroup>
                    </SelectContent>
                </Select>
            </div>

            {/* Citation Intensity (Use radio buttons instead) */}
            <div className="flex flex-col gap-2">
                <label className="text-[18px] font-semibold text-[#212121]">How Citation-Happy Should We Be?</label>
                <div className="flex flex-col gap-2">
                    <label className="flex items-center gap-2 text-[16px] text-[#9E9E9E]">
                        <input type="radio" name="citation-intensity" value="essentials" onChange={(e) => setCitationIntensity(e.target.value)}
                        />
                        Just the Essentials (when less is more)
                    </label>
                    <label className="flex items-center gap-2 text-[16px] text-[#9E9E9E]">
                        <input type="radio" name="citation-intensity" value="balanced" onChange={(e) => setCitationIntensity(e.target.value)}
                        />
                        Balanced Approach (recommended for most papers)
                    </label>
                    <label className="flex items-center gap-2 text-[16px] text-[#9E9E9E]">
                        <input type="radio" name="citation-intensity" value="everything" onChange={(e) => setCitationIntensity(e.target.value)}
                        />
                        Cite Everything (for when your grade depends on it)
                    </label>
                </div>
            </div>

            {/* Additional Instructions */}
            <div className="flex flex-col gap-2">
                <h4 className="text-[18px] font-semibold text-[#212121]">Got Any Special Instructions?</h4>
                <p className="text-[16px] text-[#8A8A8A]">
                    (Like &quot;only use journal articles&quot; or &quot;my professor is extremely picky about page numbers&quot;)
                </p>
            </div>

            {/* CTA Button */}
            <button
                onClick={onWorkMagic}
                className="mb-16 w-full self-start rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-semibold">
                Work Your Citation Magic
            </button>
        </div>
    );
};

export default CitationCustomizationStation;
