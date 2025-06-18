import React, { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import { CheckCircle2Icon, DownloadCloudIcon } from 'lucide-react'
import { toast } from 'sonner';
import { createSubscription } from '@/service/subscriptionService';
import axios from 'axios';

import FlutterwaveButton from './FlutterWaveButton';


type CitationPerfectionAchieveProps = {
    // documentUrl: string | null;       // Still useful for a direct link if needed, or as a fallback
    onDownloadClick: () => void;   // Function to trigger download from processor
    citationCount: number;
    referenceCount: number;
    setIsCitationPerfectionAchieved: (value: boolean) => void;
    // hoursSaved?: number; // Optional
};

const CitationPerfectionAchieve: React.FC<CitationPerfectionAchieveProps> = ({
    // documentUrl,
    onDownloadClick,
    citationCount,
    referenceCount,
    setIsCitationPerfectionAchieved
}) => {

    const [country, setCountry] = useState<string | null>(null);
    const [currency, setCurrency] = useState<'NGN' | 'USD'>('USD');
    const [isLoading, setIsLoading] = useState(false);
    const [token, setToken] = useState<string | null>(null);
    const [email, setEmail] = useState<string | null>(null)
    const [register, setRegister] = useState(false)

    const modalRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (modalRef.current && !modalRef.current.contains(event.target as Node)) {
                setIsCitationPerfectionAchieved(false); // Close modal by setting to false
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [setIsCitationPerfectionAchieved]);
    useEffect(() => {
        // Only access localStorage after the component has mounted
        const storedToken = typeof window !== 'undefined' ? localStorage.getItem("token") : null;
        setToken(storedToken);
        const storedEmail = typeof window !== 'undefined' ? localStorage.getItem("userEmail") : null;
        setEmail(storedEmail);
    }, []);

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

    // Monthly Plan
    const monthlyPrice = currency === 'NGN' ? 15000 : 15;

    // Enterprise Plan
    const enterprisePrice = currency === 'NGN' ? 70000 : 70;

    const handleAuthenticationRequired = (planType: string) => {
        if (!token || !email) {
            toast.info(`Please log in to subscribe to the ${planType} plan`);
            if (setRegister) {
                setRegister(true);
            }
            return false;
        }
        return true;
    };

    const handlePaymentSuccessful = async (planType: 'monthly' | 'enterprise', maxRetries = 3) => {
        if (!email) {
            toast.error("User information not available");
            return;
        }
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                setIsLoading(true);
                const payload = {
                    name: planType === 'monthly' ? "Monthly Plan" : "Enterprise Plan",
                    description: planType === 'monthly' ? "Monthly subscription with unlimited access" : "Enterprise plan with premium features",
                    price: planType === 'monthly' ? (currency === 'NGN' ? 15000 : 15) : (currency === 'NGN' ? 70000 : 70),
                    duration: planType === 'monthly' ? "monthly" : "yearly",
                    features: planType === 'monthly'
                        ? ["Unlimited document uploads, AI-powered citations, Multiple citation styles (APA, MLA, Chicago, etc.), Priority processing"]
                        : ["Everything in Monthly Plan, Dedicated support, Team collaboration features, Custom integrations"],
                };
                const res = await createSubscription(payload);
                if (res?.data?.status === "success") {
                    toast.success(`${planType === 'monthly' ? 'Monthly' : 'Enterprise'} subscription activated successfully!`);
                }
            } catch (error: any) {
                console.error('Subscription creation error:', error);
                const message = error?.response?.data?.message || error?.message || "Failed to activate subscription. Please contact support.";
                toast.error(message);
            } finally {
                setIsLoading(false);
            }
        }
    };

    const renderSubscriptionButton = (planType: 'monthly' | 'enterprise', buttonClass: string) => {
        const price = planType === 'monthly' ? monthlyPrice : enterprisePrice;
        const buttonText = planType === 'monthly' ? "Subscribe Now" : "Upgrade Now";

        if (!token || !email) {
            return (
                <button
                    onClick={() => handleAuthenticationRequired(planType === 'monthly' ? 'Monthly' : 'Enterprise')}
                    className={buttonClass}
                    disabled={isLoading}
                >
                    {buttonText}
                </button>
            );
        }

        return (
            <FlutterwaveButton
                email={email}
                amount={price}
                name={`Customer ${email}`}
                phone={''}
                currency={"NGN"}
                onSuccess={() => handlePaymentSuccessful(planType)}
                buttonText={isLoading ? "Processing..." : buttonText}
                className={`${buttonClass} ${isLoading ? 'cursor-not-allowed opacity-50' : ''}`}
            />
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center overflow-y-scroll bg-black bg-opacity-70 p-4 text-[#545454]">
            <div
                ref={modalRef}
                className="my-auto flex w-[95%] flex-col items-center rounded-lg bg-white p-6 shadow-lg sm:max-w-[811px]">
                <div className='mb-4 h-[87px] w-full'>
                    <img src="/gif/Animation - success.gif" alt="gif" className='size-full object-fill' />
                </div>
                <div className='flex w-full flex-col gap-4'>
                    <p className='text-center text-2xl font-semibold text-[#333333]'>Citation Perfection Achieved!</p>
                    <ul className='flex flex-col gap-2 text-sm text-[#9E9E9E] sm:text-base'>
                        <li className='flex w-full items-start gap-3' key="in-text-citations">
                            <img src="/assets/tick-circle.svg" alt="tick" className='mt-1 size-5 shrink-0' />
                            <p>We&apos;ve added <strong>{citationCount}</strong> in-text citations.</p>
                        </li>
                        <li className='flex w-full items-start gap-3' key="reference-entries">
                            <img src="/assets/tick-circle.svg" alt="tick" className='mt-1 size-5 shrink-0' />
                            <p>Created <strong>{referenceCount}</strong> reference entries.</p>
                        </li>
                        <li className='flex w-full items-start gap-3' key="hours-saved">
                            <img src="/assets/tick-circle.svg" alt="tick" className='mt-1 size-5 shrink-0' />
                            <p>And saved you approximately [Hours] hours of formatting!</p>
                        </li>
                    </ul>
                    <div className='mt-4 flex flex-col gap-3'>
                        <label className='text-lg font-semibold text-[#333333]'>File type</label>
                        <div className='flex w-full items-center justify-between rounded-lg border border-[#E0E0E0] bg-[#FAFAFA] p-4 text-base outline-none'>
                            <div className='flex items-center gap-3'>
                                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                    className="lucide lucide-file-text text-[#31DAC0]"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><line x1="10" y1="9" x2="8" y2="9"></line></svg>
                                <p className='text-[#545454]'>Word Document (.docx)</p>
                            </div>
                            {/* <ChevronDown className="text-gray-500" />
                            File type selection can be a future feature */}
                        </div>

                        <button
                            onClick={onDownloadClick} // Use the passed download handler
                            className='flex w-full items-center justify-center gap-2 rounded-full bg-[#31DAC0] px-6 py-3.5 text-base font-semibold text-[#010F34] transition-colors hover:bg-[#28bfa8]'
                        >
                            <DownloadCloudIcon size={20} />
                            Download Your Citation Masterpiece
                        </button>

                        {/* Fallback link using documentUrl if onDownloadClick is not provided (though it should be) */}
                        <p className='mt-1 text-center text-xs text-[#9E9E9E]'>Available as: .docx (Word Document)</p>
                    </div>
                </div>
                {/* Pricing/Share section - ensure keys are correct for mapped elements */}
                <div className='mt-8 flex w-full flex-col items-center gap-6'>
                    <div className='flex w-full flex-col gap-4 rounded-lg bg-[#F7F7F7] p-4 sm:p-6'>
                        <p className='text-lg font-semibold text-[#333333]'>Know another writer drowning in citations?</p>
                        <p className='text-sm text-[#8A91A2] sm:text-base'>Share Tweakr and help them achieve citation perfection too!</p>
                        <div className='flex flex-wrap items-center justify-center gap-3 sm:justify-start sm:gap-4'>
                            {["facebook", "twitch", "instagram", "twitter", "circum_linkedin"].map(social => (
                                <div className='flex cursor-pointer items-center justify-center rounded-full bg-white p-3 shadow transition-shadow hover:shadow-md sm:p-4' key={social}>
                                    <img src={`/assets/${social}.svg`} alt={social} className="size-5 sm:size-6" />
                                </div>
                            ))}
                        </div>
                    </div>
                    <p className='mt-4 text-lg font-medium text-[#333333]'>More papers in your future? Upgrade for unlimited power!</p>
                    <motion.section
                        className="flex w-full flex-col items-center justify-center gap-8"
                        initial={{ opacity: 0, y: 50 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: "easeOut" }}
                    >
                        <motion.div className="grid w-full grid-cols-1 gap-6 sm:gap-8 md:grid-cols-2">
                            {/* Monthly Plan */}
                            <motion.div
                                initial={{ opacity: 0, y: 50 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: 1 * 0.2, duration: 0.6, ease: "easeOut" }}
                                className="flex flex-col justify-between overflow-hidden rounded-2xl border bg-[#155C51] p-6 text-white shadow-lg sm:p-8"
                            >
                                <div className="text-center">
                                    <h3 className="text-xl font-semibold sm:text-2xl">Monthly Plan</h3>
                                    <p className="mt-2 text-2xl font-bold sm:text-3xl">
                                        {currency === 'NGN' ? '₦15,000' : '$15'}
                                    </p>
                                    <p className="mt-1 text-xs sm:text-sm">Per month</p>
                                </div>
                                <div className="mt-6">
                                    {renderSubscriptionButton(
                                        'monthly',
                                        'z-[9999] w-full rounded-full bg-white py-3 text-sm font-semibold text-[#010F34] transition-all hover:bg-gray-100 sm:text-base'
                                    )}
                                </div>
                                <div className="mt-6 flex flex-col gap-3">
                                    {[
                                        "Unlimited document uploads",
                                        "AI-powered citations",
                                        "Multiple citation styles (APA, MLA, Chicago, etc.)",
                                        "Priority processing",
                                    ].map((feature) => (
                                        <div className="flex items-start gap-3" key={feature}>
                                            <CheckCircle2Icon className="size-5 shrink-0 text-white sm:size-6" />
                                            <p className="text-sm sm:text-base">{feature}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>

                            {/* Enterprise Plan */}
                            <motion.div
                                initial={{ opacity: 0, y: 50 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                transition={{ delay: 2 * 0.2, duration: 0.6, ease: "easeOut" }}
                                className="flex flex-col justify-between overflow-hidden rounded-2xl border bg-white p-6 text-[#155C51] shadow-lg sm:p-8"
                            >
                                <div className="text-center">
                                    <h3 className="text-xl font-semibold sm:text-2xl">Enterprise</h3>
                                    <p className="mt-2 text-2xl font-bold sm:text-3xl">
                                        {currency === 'NGN' ? '₦70,000' : '$70'}
                                    </p>
                                    <p className="mt-1 text-xs sm:text-sm">Per month</p>
                                </div>
                                <div className="mt-6">
                                    {renderSubscriptionButton(
                                        'enterprise',
                                        'z-[9999] w-full rounded-full bg-[#31DAC0] py-3 text-sm font-semibold text-[#010F34] transition-all hover:bg-[#28bfa8] sm:text-base'
                                    )}
                                </div>
                                <div className="mt-6 flex flex-col gap-3">
                                    {[
                                        "Everything in the Monthly Plan",
                                        "Dedicated support",
                                        "Team collaboration features",
                                        "Custom integrations",
                                    ].map((feature) => (
                                        <div className="flex items-start gap-3" key={feature}>
                                            <CheckCircle2Icon className="size-5 shrink-0 text-[#31DAC0] sm:size-6" />
                                            <p className="text-sm sm:text-base">{feature}</p>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        </motion.div>
                    </motion.section>
                </div>
            </div>
        </div>
    )
}

export default CitationPerfectionAchieve