import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Minus } from "lucide-react";


const dommyfaqs = [
    {
        question: "Who is a Mentee?",
        answer: "A mentee is an individual who seeks guidance and mentorship from an experienced professional to develop skills and achieve career goals.",
    },
    {
        question: "How can I become a mentor?",
        answer: "To become a mentor, you need to sign up on our platform, complete your profile, and apply to become a mentor in your field of expertise.",
    },
    {
        question: "Is the mentorship program free?",
        answer: "Yes, our mentorship program is free for all mentees. Mentors volunteer their time to help guide aspiring professionals.",
    },
    {
        question: "How do I connect with a mentor?",
        answer: "Once registered, you can browse mentor profiles, send a request, and schedule sessions based on availability.",
    },
];
const FAQs = () => {
    const [activeIndex, setActiveIndex] = useState<number | null>(null);

    const toggleFAQ = (index: number) => {
        setActiveIndex(activeIndex === index ? null : index);
    };
    return (
        <div className="relative flex flex-col items-start justify-center gap-10 px-8 py-28 sm:flex-row">
            <motion.div
                className='flex w-full flex-col gap-4 sm:max-w-[400px]'
                initial={{ opacity: 0, x: -50, y: -50 }}
                whileInView={{ opacity: 1, x: 0, y: 0 }}
                // viewport={{ once: true }}
                transition={{ duration: 0.8 }}
            >
                <h1 className='text-[40px] font-semibold'>FAQ</h1>
                <p className='text-[18px] text-[#333333]'>As a students or academician, you’re overwhelmed with multiple files, documents, articles, blogs, making it hard to reference.</p>
            </motion.div>

            <motion.div
                className="flex w-full flex-col gap-8 sm:w-[840px]"
                initial={{ opacity: 0, x: 50, y: -50 }}
                whileInView={{ opacity: 1, x: 0, y: 0 }}
                // viewport={{ once: true }}
                transition={{ duration: 0.8 }}
            >
                {dommyfaqs.map((faq, index) => (
                    <div key={index} className="w-full rounded-2xl border border-[#EAEBEB] bg-[#EDEDED] p-4 text-[#333333]  sm:p-6 ">
                        <button
                            className="flex w-full items-center justify-between text-left text-lg font-semibold md:text-[24px]"
                            onClick={() => toggleFAQ(index)}
                        >
                            {faq.question}
                            <div className="flex items-center justify-center rounded-full bg-[#010F34] p-2 text-[#EDEDED]">
                                {activeIndex === index ? (
                                    <Minus className="size-5" />
                                ) : (
                                    <Plus className="size-5" />
                                )}
                            </div>
                        </button>

                        <AnimatePresence>
                            {activeIndex === index && (
                                <motion.div
                                    initial={{ opacity: 0, height: 0 }}
                                    animate={{ opacity: 1, height: "auto" }}
                                    exit={{ opacity: 0, height: 0 }}
                                    className="mt-6 overflow-hidden  text-justify text-sm md:text-[18px]"
                                >
                                    {faq.answer}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                ))}
            </motion.div >
        </div>
    )
}

export default FAQs
