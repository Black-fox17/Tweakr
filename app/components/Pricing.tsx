import { CheckCircle2Icon } from "lucide-react";
import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import FlutterwaveButton from './FlutterWaveButton';
import { createSubscription } from "@/service/subscriptionService";
import Link from "next/link";
import axios from "axios";

const containerVariants = {
    hidden: {},
    show: {
        transition: {
            staggerChildren: 0.2,
        },
    },
};

type PricingProps = {
    setIsRegisterReady: (ready: boolean) => void;
};

const Pricing: React.FC<PricingProps> = ({ setIsRegisterReady }) => {
    const [country, setCountry] = useState<string | null>(null);
    const [currency, setCurrency] = useState<'NGN' | 'USD'>('USD');
    const [isLoading, setIsLoading] = useState(false);
    const [token, setToken] = useState<string | null>(null);
    const [email, setEmail] = useState<string | null>(null)


    // Function to navigate to hero section
    const navigateToHero = () => {
        const heroElement = document.querySelector('#hero') || document.querySelector('[data-hero]');
        if (heroElement) {
            heroElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
            // Fallback: scroll to top of page
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

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
                // Add timeout to location fetch to prevent hanging
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

                const res = await axios.get('https://ipapi.co/json/', {
                    signal: controller.signal,
                    timeout: 8000
                });

                clearTimeout(timeoutId);
                const userCountry = res?.data?.country_name;
                setCountry(userCountry);

                if (userCountry === 'Nigeria') {
                    setCurrency('NGN');
                } else {
                    setCurrency('USD');
                }
            } catch (error: any) {
                console.error('Error fetching location:', error);
                if (error.name === 'AbortError') {
                    console.log('Location fetch timeout - using default currency');
                } else if (!navigator.onLine) {
                    toast.error("Unable to detect location due to network issues. Using default currency (USD).");
                }
                setCurrency('USD'); // Default fallback
            }
        };

        fetchLocation();
    }, []);


    // Monthly Plan
    const monthlyPrice = currency === 'NGN' ? 15000 : 15;

    // Enterprise Plan
    const enterprisePrice = currency === 'NGN' ? 70000 : 70;

    const handleAuthenticationRequired = (planType: string, e?: React.MouseEvent) => {
        // Prevent default behavior if event is provided
        if (e) {
            e.preventDefault();
            e.stopPropagation();
        }

        if (!token || !email) {
            navigateToHero()
            toast.info(`Please log in to subscribe to the ${planType} plan`);
            setIsRegisterReady(true);
            return false;
        }
        return true;
    };

    const handlePaymentSuccessful = async (planType: 'monthly' | 'enterprise', maxRetries = 3) => {
        if (!email) {
            toast.error("User information not available");
            return;
        }

        // Check network connectivity before making API calls
        if (!navigator.onLine) {
            navigateToHero();
            toast.error("No internet connection. Please check your network and try again.");
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
                    navigateToHero();
                    toast.success(`${planType === 'monthly' ? 'Monthly' : 'Enterprise'} subscription activated successfully!`);
                }
            } catch (error: any) {
                navigateToHero()
                console.error('Subscription creation error:', error);

                // Check if it's a network error
                if (error.name === 'NetworkError' ||
                    error.code === 'NETWORK_ERROR' ||
                    !navigator.onLine ||
                    error.message?.toLowerCase().includes('network') ||
                    error.message?.toLowerCase().includes('connection')) {

                    if (attempt === maxRetries) {
                        toast.error("Network error: Unable to activate subscription. Please check your connection and contact support.");
                    }
                } else {
                    const message = error?.response?.data?.message || error?.message || "Failed to activate subscription. Please contact support.";
                    toast.error(message);
                    break; // Don't retry for non-network errors
                }

                // Add delay before retry (except on last attempt)
                if (attempt < maxRetries) {
                    await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
                }
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
                    onClick={(e) => handleAuthenticationRequired(planType === 'monthly' ? 'Monthly' : 'Enterprise', e)}
                    className={buttonClass}
                    disabled={isLoading}
                    style={{
                        userSelect: 'none',
                        WebkitUserSelect: 'none'
                    }}
                >
                    {buttonText}
                </button>
            );
        }

        return (
            <FlutterwaveButton
                email={email}
                amount={200}
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
        <motion.section
            id="pricing"
            className="flex flex-col items-center justify-center gap-16 px-6 py-20"
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
            viewport={{ once: true, amount: 0.2 }}
        >
            {/* Header */}
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="max-w-3xl text-center"
            >
                <h2 className="text-4xl font-bold text-gray-900">Pricing</h2>
                <p className="mt-2 text-lg text-gray-600">
                    Pricing That Makes Cents <span className="font-mono">¢</span> (And Saves Dollars)
                </p>
                {/* {!token && toast.message("Please log in to subscribe to our plans")} */}
            </motion.div>

            {/* Network Status Indicator (optional) */}
            {!navigator.onLine && (
                <div className="mb-4 rounded-lg border border-red-200 bg-red-50 p-4 text-center">
                    <p className="text-sm text-red-700">
                        ⚠️ You appear to be offline. Please check your internet connection to complete payments.
                    </p>
                </div>
            )}


            {/* Pricing Cards */}
            <motion.div
                className="grid w-full max-w-7xl grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3"
                variants={containerVariants}
            >
                {/* Pay-As-You-Go Plan */}
                <motion.div
                    initial={{ opacity: 0, y: 50 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0 * 0.2, duration: 0.6, ease: "easeOut" }}
                    className="flex flex-col justify-between overflow-hidden rounded-2xl border bg-white p-6 text-[#155C51] shadow-lg sm:p-8"
                >
                    <div className="text-center">
                        <h3 className="text-xl font-semibold sm:text-2xl">Pay-As-You-Go</h3>
                        <p className="mt-2 text-2xl font-bold sm:text-3xl">
                            {currency === 'NGN' ? '₦1,000' : '$1.0'}
                        </p>
                        <p className="mt-1 text-xs sm:text-sm">Per document</p>
                    </div>
                    <Link href="/dashboard" className="z-[9999] mt-6 block w-full">
                        <button
                            type="button"
                            className="w-full rounded-full bg-[#31DAC0] py-3 text-sm font-semibold text-[#010F34] transition-all hover:bg-[#28bfa8] sm:text-base"
                            style={{
                                userSelect: 'none',
                                WebkitUserSelect: 'none'
                            }}
                        >
                            Get Started
                        </button>
                    </Link>
                    <div className="mt-6 flex flex-col gap-3">
                        {[
                            "2000 words document",
                            "One-time payment per document",
                            "Instant referencing",
                            "No subscription required",
                            "Full access to citation tools",
                        ].map((feature) => (
                            <div className="flex items-start gap-3" key={feature}>
                                <CheckCircle2Icon className="size-5 shrink-0 text-[#31DAC0] sm:size-6" />
                                <p className="text-sm sm:text-base">{feature}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>

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
    );
};

export default Pricing;