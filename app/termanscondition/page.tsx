import React from 'react';
import { FileText, Shield, Settings, AlertTriangle, RefreshCw, XCircle } from 'lucide-react';

const TermsAndConditions = () => {
    const sections = [
        {
            title: "Acceptance of Terms",
            icon: <FileText className="size-5" />,
            content: "By accessing and using Tweakrr, you agree to comply with our terms and conditions. If you do not agree, you may not use the platform."
        },
        {
            title: "User Responsibilities",
            icon: <Shield className="size-5" />,
            content: "Users must ensure that the documents uploaded comply with copyright laws and are free of sensitive or illegal content."
        },
        {
            title: "Service Scope",
            icon: <Settings className="size-5" />,
            content: "Tweakrr automates in-text citations and reference list generation. It does not add, subtract, or alter document content except for citation purposes."
        },
        {
            title: "Customization Features",
            icon: <Settings className="size-5" />,
            content: "Users can select preferred reference formats. Tweakrr reserves the right to update these features periodically."
        },
        {
            title: "Limitation of Liability",
            icon: <AlertTriangle className="size-5" />,
            content: "Tweakrr is not liable for any errors in citations due to incomplete or inaccurate information in the user's uploaded documents."
        },
        {
            title: "Modifications to Terms",
            icon: <RefreshCw className="size-5" />,
            content: "Tweakrr reserves the right to update its terms at any time. Continued use of the platform signifies acceptance of the updated terms."
        },
        {
            title: "Refund Policy",
            icon: <XCircle className="size-5" />,
            content: "According to Tweakrr's terms and conditions, once a subscription or one-time payment has been made, refunds are not provided. This policy includes all purchases made through the platform."
        }
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 px-4 py-12 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-4xl">
                {/* Header */}
                <div className="mb-12 text-center">
                    <div className="mb-6 inline-flex size-16 items-center justify-center rounded-full bg-blue-600">
                        <FileText className="size-8 text-white" />
                    </div>
                    <h1 className="mb-4 text-4xl font-bold text-gray-900">
                        Terms and Conditions
                    </h1>
                    <p className="mx-auto max-w-2xl text-xl text-gray-600">
                        Please read these terms carefully before using the Tweakrr platform
                    </p>
                </div>

                {/* Terms Content */}
                <div className="overflow-hidden rounded-2xl bg-white shadow-xl">
                    <div className="p-8 sm:p-12">
                        <div className="space-y-8">
                            {sections.map((section, index) => (
                                <div
                                    key={index}
                                    className="group rounded-xl border border-transparent p-6 transition-all duration-300 hover:border-gray-200 hover:bg-gray-50"
                                >
                                    <div className="flex items-start space-x-4">
                                        <div className="shrink-0">
                                            <div className="flex size-10 items-center justify-center rounded-lg bg-blue-100 text-blue-600 transition-colors duration-300 group-hover:bg-blue-200">
                                                {section.icon}
                                            </div>
                                        </div>
                                        <div className="flex-1">
                                            <h2 className="mb-3 text-xl font-semibold text-gray-900">
                                                {section.title}
                                            </h2>
                                            <p className="leading-relaxed text-gray-700">
                                                {section.content}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="border-t border-gray-200 bg-gray-50 p-8 sm:px-12">
                        <div className="text-center">
                            <p className="mb-4 text-sm text-gray-600">
                                Last updated: {new Date().toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })}
                            </p>
                            <p className="text-xs text-gray-500">
                                By continuing to use Tweakrr, you acknowledge that you have read, understood, and agree to be bound by these terms and conditions.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TermsAndConditions;