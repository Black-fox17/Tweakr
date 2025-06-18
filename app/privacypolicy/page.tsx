import React from 'react';
import { Shield, Database, Settings, Lock, Share2, Bell } from 'lucide-react';

interface Section {
    title: string;
    icon: React.ReactElement;
    content: string;
    highlight: string;
}

type HighlightType = 'minimal-collection' | 'temporary-storage' | 'security' | 'limited-sharing' | 'updates';

const PrivacyPolicy: React.FC = () => {
    const sections: Section[] = [
        {
            title: "Data Collection",
            icon: <Database className="size-5" />,
            content: "Tweakrr collects and processes documents uploaded by users solely for citation and referencing purposes. No other content is analyzed or stored beyond this scope.",
            highlight: "minimal-collection"
        },
        {
            title: "User Preferences",
            icon: <Settings className="size-5" />,
            content: "The system allows users to customize citation years and formats. This data is temporarily stored to provide the requested service.",
            highlight: "temporary-storage"
        },
        {
            title: "Data Security",
            icon: <Lock className="size-5" />,
            content: "We ensure the safety and privacy of your uploaded documents.",
            highlight: "security"
        },
        {
            title: "Third-Party Integrations",
            icon: <Share2 className="size-5" />,
            content: "Tweakrr uses trusted citation databases for sourcing references. No user data is shared with these databases beyond what is necessary for citation matching.",
            highlight: "limited-sharing"
        },
        {
            title: "Policy Updates",
            icon: <Bell className="size-5" />,
            content: "Changes to the privacy policy will be communicated through the platform. Continued use indicates acceptance of any updates.",
            highlight: "updates"
        }
    ];

    const getHighlightStyle = (highlight: string): string => {
        const styles: Record<HighlightType, string> = {
            'minimal-collection': 'border-green-200 bg-green-50 hover:bg-green-100',
            'temporary-storage': 'border-blue-200 bg-blue-50 hover:bg-blue-100',
            'security': 'border-purple-200 bg-purple-50 hover:bg-purple-100',
            'limited-sharing': 'border-orange-200 bg-orange-50 hover:bg-orange-100',
            'updates': 'border-gray-200 bg-gray-50 hover:bg-gray-100'
        };
        return styles[highlight as HighlightType] || 'border-gray-200 bg-gray-50 hover:bg-gray-100';
    };

    const getIconStyle = (highlight: string): string => {
        const styles: Record<HighlightType, string> = {
            'minimal-collection': 'bg-green-100 text-green-600 group-hover:bg-green-200',
            'temporary-storage': 'bg-blue-100 text-blue-600 group-hover:bg-blue-200',
            'security': 'bg-purple-100 text-purple-600 group-hover:bg-purple-200',
            'limited-sharing': 'bg-orange-100 text-orange-600 group-hover:bg-orange-200',
            'updates': 'bg-gray-100 text-gray-600 group-hover:bg-gray-200'
        };
        return styles[highlight as HighlightType] || 'bg-gray-100 text-gray-600 group-hover:bg-gray-200';
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 px-4 py-12 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-4xl">
                {/* Header */}
                <div className="mb-12 text-center">
                    <div className="mb-6 inline-flex size-16 items-center justify-center rounded-full bg-indigo-600">
                        <Shield className="size-8 text-white" />
                    </div>
                    <h1 className="mb-4 text-4xl font-bold text-gray-900">
                        Privacy Policy
                    </h1>
                    <p className="mx-auto max-w-2xl text-xl text-gray-600">
                        Your privacy is our priority. Learn how we protect and handle your data.
                    </p>
                </div>

                {/* Privacy Highlights */}
                <div className="mb-12 grid gap-6 md:grid-cols-3">
                    <div className="rounded-xl border-l-4 border-green-500 bg-white p-6 shadow-lg">
                        <div className="mb-3 flex items-center">
                            <Database className="mr-2 size-6 text-green-600" />
                            <h3 className="font-semibold text-gray-900">Minimal Data</h3>
                        </div>
                        <p className="text-sm text-gray-600">Only documents for citations</p>
                    </div>
                    <div className="rounded-xl border-l-4 border-purple-500 bg-white p-6 shadow-lg">
                        <div className="mb-3 flex items-center">
                            <Lock className="mr-2 size-6 text-purple-600" />
                            <h3 className="font-semibold text-gray-900">Secure Storage</h3>
                        </div>
                        <p className="text-sm text-gray-600">Your documents are protected</p>
                    </div>
                    <div className="rounded-xl border-l-4 border-blue-500 bg-white p-6 shadow-lg">
                        <div className="mb-3 flex items-center">
                            <Share2 className="mr-2 size-6 text-blue-600" />
                            <h3 className="font-semibold text-gray-900">Limited Sharing</h3>
                        </div>
                        <p className="text-sm text-gray-600">No unnecessary data sharing</p>
                    </div>
                </div>

                {/* Privacy Policy Content */}
                <div className="overflow-hidden rounded-2xl bg-white shadow-xl">
                    <div className="p-8 sm:p-12">
                        <div className="space-y-6">
                            {sections.map((section: Section, index: number) => (
                                <div
                                    key={index}
                                    className={`group rounded-xl border-2 p-6 transition-all duration-300 ${getHighlightStyle(section.highlight)}`}
                                >
                                    <div className="flex items-start space-x-4">
                                        <div className="shrink-0">
                                            <div className={`flex size-10 items-center justify-center rounded-lg transition-colors duration-300 ${getIconStyle(section.highlight)}`}>
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
                                We are committed to protecting your privacy and will notify you of any changes to this policy.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PrivacyPolicy;