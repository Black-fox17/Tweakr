'use client';

import React, { useState } from 'react';
import { useFlutterwave, closePaymentModal } from 'flutterwave-react-v3';
import { toast } from 'sonner';
import { verifyAllPayment } from '@/service/subscriptionService';

interface FlutterwaveButtonProps {
    email: string;
    amount: number;
    name: string;
    phone: string;
    currency: string;
    onSuccess: (response: Record<string, any>) => void;
    buttonText?: string;
    className?: string;
}

const FlutterwaveButton: React.FC<FlutterwaveButtonProps> = ({
    email,
    amount,
    name = `customer ${email}`,
    phone = `phone ${email}`,
    currency,
    onSuccess,
    buttonText,
    className
}) => {
    const [isVerifying, setIsVerifying] = useState(false);
    const [isInitializing, setIsInitializing] = useState(false);

    const config = {
        public_key: process.env.NEXT_PUBLIC_FLUTTERWAVE_PUBLIC_KEY!,
        tx_ref: `TXN_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        amount,
        currency,
        payment_options: 'card,ussd,banktransfer',
        customer: {
            email: email.trim().toLowerCase(),
            phone_number: phone || `+234${Math.random().toString().substr(2, 10)}`,
            name: name || `Customer ${email.split('@')[0]}`,
        },
        customizations: {
            title: 'Tweakrr Citation Payment',
            description: 'Payment for citation processing',
            logo: '/assets/logo.svg',
            contact: {
                email: 'tweakr01@gmail.com',
                phone: '+2347062561696',
                address: 'Oluwatedo,Zone 2, Akogi Street, Oloko, Apata, Ibadan,Nigeria'
            }
        },
    };

    const handleFlutterPayment = useFlutterwave(config);

    // Check network connectivity
    const checkNetworkConnection = (): boolean => {
        if (!navigator.onLine) {
            toast.error("No internet connection. Please check your network and try again.");
            return false;
        }
        return true;
    };

    // Test API connectivity before initiating payment
    const testApiConnectivity = async (): Promise<boolean> => {
        try {
            // Simple connectivity test - you can replace this with a lightweight API call
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 5000); // 5 second timeout

            await fetch('https://api.flutterwave.com/v3/payments', {
                method: 'HEAD', // HEAD request is lighter than GET
                signal: controller.signal,
            });
            clearTimeout(timeoutId);
            return true;
        } catch (error) {
            console.error('API connectivity test failed:', error);
            return false;
        }
    };

    const verifyPaymentWithRetry = async (transactionId: number, maxRetries = 3) => {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                // console.log(`Payment verification attempt ${attempt} for transaction: ${transactionId}`);

                if (attempt > 1) {
                    await new Promise(resolve => setTimeout(resolve, 2000 * attempt));
                }

                const res = await verifyAllPayment(transactionId);

                if (res?.data?.status === 'success' ||
                    res?.data?.data?.status === 'successful' ||
                    res?.data?.message?.toLowerCase().includes('success')) {

                    toast.success("Payment verified successfully!");
                    onSuccess(res);
                    return true;
                }

                if (attempt === maxRetries) {
                    throw new Error(res?.data?.message || `Payment verification failed after ${maxRetries} attempts`);
                }

            } catch (error: any) {
                if (attempt === maxRetries) {
                    if (error.name === 'NetworkError' ||
                        error.code === 'NETWORK_ERROR' ||
                        !navigator.onLine ||
                        error.message?.toLowerCase().includes('network') ||
                        error.message?.toLowerCase().includes('connection')) {
                        toast.error("Network error during verification. Please check your connection and contact support if payment was deducted.");
                    } else {
                        toast.error(error.message || "Payment verification failed. Please contact support if payment was deducted.");
                    }
                    return false;
                }
            }
        }
        return false;
    };

    const handlePaymentClick = async (e: React.MouseEvent<HTMLButtonElement>) => {
        // Prevent default behavior and stop event propagation to prevent scrolling
        e.preventDefault();
        e.stopPropagation();

        // Prevent multiple clicks during processing
        if (isVerifying || isInitializing) {
            toast.info("Payment processing in progress, please wait...");
            return;
        }

        // Check network connectivity first
        if (!checkNetworkConnection()) {
            return;
        }

        setIsInitializing(true);

        try {
            // Test API connectivity before showing Flutterwave modal
            toast.info("Initializing payment...");

            const isConnected = await testApiConnectivity();
            if (!isConnected) {
                toast.error("Unable to connect to payment service. Please check your internet connection and try again.");
                return;
            }

            // If connectivity is good, proceed with Flutterwave
            handleFlutterPayment({
                callback: async (response) => {
                    const transactionId = response.transaction_id;
                    setIsVerifying(true);
                    try {
                        const isPaymentSuccessful =
                            response.status === "completed" ||
                            response.status === "successful" ||
                            response.status === "success";
                        if (isPaymentSuccessful && transactionId) {
                            toast.info("Payment completed! Verifying...");
                            await verifyPaymentWithRetry(transactionId);
                        } else {
                            console.error('Payment not successful:', response);
                            toast.error(`Payment ${response.status || 'failed'}. Please try again.`);
                        }
                    } catch (error: any) {
                        console.error("Error in payment callback:", error);
                        if (error.message?.toLowerCase().includes('network') ||
                            error.name === 'NetworkError' ||
                            !navigator.onLine) {
                            toast.error("Network error occurred. Please check your connection and contact support if payment was deducted.");
                        } else {
                            toast.error("An unexpected error occurred during payment processing.");
                        }
                    } finally {
                        setIsVerifying(false);
                        closePaymentModal();
                    }
                },
                onClose: () => {
                    if (!isVerifying) {
                        toast.info("Payment cancelled.");
                    }
                    setIsVerifying(false);
                },
            });

        } catch (error: any) {
            console.error("Error initializing payment:", error);
            if (error.message?.toLowerCase().includes('network') ||
                error.name === 'NetworkError' ||
                !navigator.onLine) {
                toast.error("Network error: Unable to initialize payment. Please check your internet connection.");
            } else {
                toast.error("Failed to initialize payment. Please try again.");
            }
        } finally {
            setIsInitializing(false);
        }
    };

    const isProcessing = isVerifying || isInitializing;

    return (
        <button
            type="button" // Explicitly set button type to prevent form submission
            onClick={handlePaymentClick}
            disabled={isProcessing}
            className={className || "flex w-full items-center gap-3 rounded-md border border-[#E0E0E0] bg-[#FAFAFA] p-4 transition-all duration-200 focus-within:border-[#31DAC0] hover:border-[#31DAC0] disabled:cursor-not-allowed disabled:opacity-50"}
            style={{
                // Prevent text selection and ensure button doesn't cause layout shifts
                userSelect: 'none',
                WebkitUserSelect: 'none',
                MozUserSelect: 'none',
                msUserSelect: 'none'
            }}
        >
            {isInitializing ? (
                <div className="flex items-center justify-center gap-4">
                    <div className="size-4 animate-spin rounded-full border-b-2 border-current"></div>
                    <span>Initializing payment...</span>
                </div>
            ) : isVerifying ? (
                <div className="flex items-center gap-2">
                    <div className="size-4 animate-spin rounded-full border-b-2 border-current"></div>
                    <span>Verifying payment...</span>
                </div>
            ) : (
                buttonText || (
                    <>
                        <img src="/assets/paypal.svg" alt="paypal" className="size-[24px] object-contain" />
                        <p className='w-full bg-transparent text-[16px] text-[#333333] outline-none placeholder:text-[#9E9E9E]'>
                            Pay Now
                        </p>
                    </>
                )
            )}
        </button>
    );
};

export default FlutterwaveButton;