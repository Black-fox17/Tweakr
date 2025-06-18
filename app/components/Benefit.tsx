import React from 'react'
import { motion } from 'framer-motion'

const cardVariants = {
    hidden: { opacity: 0, y: 40 },
    show: (i: number) => ({
        opacity: 1,
        y: 0,
        transition: {
            delay: i * 0.25,
            duration: 0.6,
            ease: "easeOut",
        },
    }),
};

const benefits = [
    {
        icon: "/assets/Clock-unwind.svg",
        title: "Hours Back in Your Life",
        text: "What would you do with an extra 3 hours? Sleep? Netflix? Actually read the sources you're citing?",
    },
    {
        icon: "/assets/Perfect A.svg",
        title: "Citation Perfection Guaranteed",
        text: "AI-driven referencing ensures every citation is correctly formatted.",
    },
    {
        icon: "/assets/Friedly-character.svg",
        title: "Works With Your Writing Weapons of Choice",
        text: "Google Docs, Word, or uploaded documents - we play nice with them all.",
    },
    {
        icon: "/assets/Style-stack.svg",
        title: "More Citation Styles Than You Knew Existed",
        text: "APA, MLA, Chicago, Harvard, IEEE, and 2,995 others you've never heard of (but might need someday).",
    },
];


const Benefit = () => {
    return (
        <div id='benefits' className='flex items-center justify-center' >
            <div className="pt-10 pb-[7rem] px-4 flex flex-col md:flex-row items-center sm:items-start justify-center sm:justify-between gap-12">
                <motion.div
                    initial={{ opacity: 0, x: -50, y: -50 }}
                    whileInView={{ opacity: 1, x: 0, y: 0 }}
                    // viewport={{ once: true }}
                    transition={{ duration: 0.8 }}
                    className="flex flex-col gap-4 max-w-[400px]">
                    <h1 className="text-[32px] sm:text-[40px] font-medium">Benefits</h1>
                    <p className="text-[16px] sm:text-[18px] text-[#333333]">Why Students & Researchers Are Saying "Thank Goodness"</p>
                </motion.div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 w-full">
                    {benefits.map((benefit, i) => (
                        <motion.article
                            key={i}
                            custom={i}
                            variants={cardVariants}
                            initial="hidden"
                            whileInView="show"
                            className="flex flex-col gap-4 max-w-full sm:max-w-[411px]"
                        >
                            <img src={benefit.icon} alt="icon" className="w-[80px] h-[80px]" />
                            <h4 className="text-[20px] sm:text-[24px] font-medium">{benefit.title}</h4>
                            <p className="text-[16px] sm:text-[18px]  text-[#333333]">{benefit.text}</p>
                        </motion.article>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Benefit
