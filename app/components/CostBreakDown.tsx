import React, { useEffect, useState } from 'react';
import axios from 'axios';
import FlutterwaveButton from './FlutterWaveButton';
import { useQuery } from '@tanstack/react-query';
import { getSingleSubscription } from '@/service/subscriptionService';

const calculatePrice = (wordCount: number): { naira: number; dollar: number } => {
    const ratePerWordNaira = 0.5;
    const ratePerWordDollar = 0.0005;
    return {
        naira: Math.ceil(wordCount * ratePerWordNaira),
        dollar: Math.ceil(wordCount * ratePerWordDollar),
    };
};




type CostBreakDownProps = {
    wordCount: number;
    acceptedCitation: number;
    handleCompleteCitationTransportation: () => void;
    setIsCitationPerfectionAchieved: (value: boolean) => void;
};



const CostBreakDown: React.FC<CostBreakDownProps> = ({
    wordCount,
    acceptedCitation,
    handleCompleteCitationTransportation,
    setIsCitationPerfectionAchieved,
}) => {
    const [country, setCountry] = useState<string | null>(null);
    const [currency, setCurrency] = useState<'NGN' | 'USD'>('USD');
    const price = calculatePrice(wordCount);

    const handleComplete = () => {
        setIsCitationPerfectionAchieved(true);
        handleCompleteCitationTransportation();
    };

    const userId = localStorage.getItem("id")
    const email = localStorage.getItem("userEmail")

    const { data: subscribptions, isPending, error: subscriptionError, refetch } = useQuery({
        queryKey: ['subscription', userId],
        queryFn: () => getSingleSubscription(userId!),
        enabled: !!userId,
        refetchOnMount: true, // ← ensures the call is made when the component mounts
    });

    useEffect(() => {
        if (userId) {
            refetch(); // Will force call the query fn again
        }
    }, []);


    const Subscribed = subscribptions?.data?.data;

    // Handle subscription error
    useEffect(() => {
        if (subscriptionError) {
            console.error('Subscription fetch error:', subscriptionError);
        }
    }, [subscriptionError]);

    useEffect(() => {
        const fetchLocation = async () => {
            try {
                const res = await axios.get('https://ipapi.co/json/');
                const userCountry = res?.data?.country_name;
                setCountry(userCountry);

                if (userCountry === 'Nigeria') {
                    setCurrency('NGN');
                } else {
                    setCurrency('USD');
                }
            } catch (error) {
                console.error('Error fetching location:', error);
                setCurrency('USD'); // Default fallback
            }
        };

        fetchLocation();
    }, []);

    const displayAmount = currency === 'NGN'
        ? (price.naira < 500 ? 500 : price.naira)
        : price.dollar;

    return (
        <div className='flex items-center justify-center'>
            <div className="flex size-full flex-col items-center justify-start gap-4 px-4 sm:mb-0">
                <h4 className="border-b-[0.5px] border-[#D8D8D8] py-4 text-[24px] font-semibold text-[#010F34]">
                    Your Citation Freedom Is Just One Step Away 👌
                </h4>

                <div className="mb-32 flex w-full flex-col items-center justify-center gap-2">
                    <div className='flex flex-col items-start justify-center'>
                        <p className="text-[18px] font-semibold text-[#333333]">The Damage Report</p>
                        <ul className="flex flex-col gap-1 text-[#9E9E9E]">
                            <li className="flex w-full items-center gap-3">
                                <img src="/assets/tick-circle.svg" alt="tick" className="size-[20px]" />
                                <p>Citations Added: {acceptedCitation}</p>
                            </li>
                            <li className="flex w-full items-center gap-3">
                                <img src="/assets/tick-circle.svg" alt="tick" className="size-[20px]" />
                                <p>Time Saved: Approximately 6 hours</p>
                            </li>
                            <li className="flex w-full items-center gap-3">
                                <img src="/assets/tick-circle.svg" alt="tick" className="size-[20px]" />
                                <p>Formatting Headaches Avoided: Countless</p>
                            </li>
                        </ul>

                        <div className="flex flex-col items-stretch justify-center gap-4 py-4 sm:flex-row">
                            <article className="flex w-full flex-col gap-2 rounded-sm border border-[#F3F3F3] p-4 text-[18px] text-[#9E9E9E] sm:max-w-[210px]">
                                <h4 className="text-[18px] font-semibold text-[#333333]">Cost Breakdown</h4>
                                <p>Base Fee: <span className="text-[#333333] ">{currency === 'NGN' ? '₦' : '$'}0.5</span></p>
                                <p>Word Count: <span className="text-[#333333] ">{wordCount}</span></p>
                                <p>Citation Magic ({acceptedCitation} citations): <span className="text-[#333333] ">
                                    {currency === 'NGN' ? '₦' : '$'}{displayAmount}
                                </span></p>
                            </article>
                            <article className="flex w-full flex-col gap-2 rounded-sm border border-[#F3F3F3] bg-[#F7F7F7] p-4 text-[18px] text-[#9E9E9E] sm:max-w-[210px]">
                                <h4 className="text-[18px] font-semibold text-[#333333]">Tweakrr:  {currency === 'NGN' ? '₦' : '$'}{displayAmount}
                                </h4>
                                <p>Coffee for a late-night citation session: <span className="text-[#333333] ">{currency === 'NGN' ? '₦' : '$'}0.00</span></p>
                                <p>Points lost for incorrect citations: <span className="text-[#333333] ">Priceless</span></p>
                            </article>
                        </div>

                        <div className="flex w-full flex-col gap-4">
                            <h4 className="text-[18px] font-semibold text-[#333333]">Continue To Payment</h4>

                            <div className="flex w-full gap-4">
                                {/* Card Option */}
                                {/* <div className="flex items-center gap-3 p-4 rounded-md bg-[#FAFAFA] border border-[#E0E0E0] transition-all duration-200 hover:border-[#31DAC0] focus-within:border-[#31DAC0] w-full">
                                <img src="/assets/card.svg" alt="card" className="w-[24px] h-[24px] object-contain" />
                                <input
                                    type="text"
                                    placeholder="Card"
                                    className="bg-transparent outline-none text-[#333333] placeholder:text-[#9E9E9E] text-[16px] w-full"
                                />
                            </div> */}

                                {/* Flutterwave (acting as PayPal substitute here) */}

                            </div>
                        </div>

                        {/* <div className="flex flex-col gap-4 text-[18px]">
                        <h4 className="text-[#333333] font-semibold text-[18px]">Card Information</h4>

                        <div>
                            <input
                                type="text"
                                placeholder="3355 4646 3737 363"
                                className="bg-[#FAFAFA] border border-[#F3F3F3] rounded-md p-4 text-[#333333] placeholder:text-[#9E9E9E] outline-none w-full"
                            />

                            <div className="flex gap-2 mt-2">
                                <input
                                    type="text"
                                    placeholder="Expiration date"
                                    className="bg-[#FAFAFA] border border-[#F3F3F3] rounded-md p-4 text-[#333333] placeholder:text-[#9E9E9E] outline-none w-full"
                                />
                                <input
                                    type="text"
                                    placeholder="Security Code"
                                    className="bg-[#FAFAFA] border border-[#F3F3F3] rounded-md p-4 text-[#333333] placeholder:text-[#9E9E9E] outline-none w-full"
                                />
                            </div>
                        </div>
                    </div> */}
                    </div>

                    <p className="mt-4 self-center text-center text-[12px] text-[#8A8A8A]">
                        Your document is under our protection. <br />
                        It will be available for download immediately after payment.
                    </p>
                    {isPending && (
                        <p className="text-[16px] text-[#31DAC0]">Loading subscription status...</p>
                    )}
                    {Subscribed && !isPending ? (
                        <button
                            onClick={handleComplete}
                            className='w-full self-start rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-semibold'>
                            Complete My Citation Transformation
                        </button>
                    )
                        : (
                            <FlutterwaveButton
                                email={email || "example@gmail.co"}
                                amount={displayAmount}
                                currency={currency}
                                name=""
                                phone=""
                                onSuccess={handleComplete}
                                buttonText='Complete My Citation Transformation'
                                className="w-full self-start rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-semibold"
                            />
                        )}
                </div>
            </div>
        </div>
    );
};

export default CostBreakDown;
