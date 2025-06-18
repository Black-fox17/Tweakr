import { motion } from "framer-motion";

const fadeInFrom = (direction: "top" | "bottom", delay = 0) => ({
    hidden: { opacity: -1, y: direction === "top" ? -100 : 100 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 1, delay, ease: "easeOut" },
    },
});

export default function HowItWorks() {
    return (
        <div
            id="about"
            className="container mx-auto flex flex-col items-center justify-center gap-8 py-10 px-4">
            {/* Image from top */}
            <motion.img
                src="/assets/Liberation.svg"
                alt="img"
                className="max-w-[358px]"
                initial="hidden"
                whileInView="visible"
                // viewport={{ once: true }}
                variants={fadeInFrom("top", 0.1)}
            />

            {/* Heading and Text from bottom */}
            <motion.div
                className="px-4 text-center flex flex-col items-center gap-3"
                initial="hidden"
                whileInView="visible"
                // viewport={{ once: true }}
                variants={fadeInFrom("bottom", 0.3)}
            >
                <h1 className="text-2xl sm:text-3xl md:text-[40px] font-semibold">How it Works?</h1>
                <p className="text-[#333333] text-base md:text-lg">
                    Three Steps to Citation Liberation
                </p>
            </motion.div>



            {/* Articles - Responsive Grid */}
            <div className="flex  flex-col lg:flex-row gap-12 lg:gap-8 relative w-full items-center justify-center">
                {/* Arrow with smooth opacity */}
                <motion.img
                    src="/assets/arrows.svg"
                    alt="arrow"
                    className="hidden md:block absolute top-[27%] left-[30%] w-[80px] lg:w-auto"
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    transition={{ duration: 3, ease: "easeInOut", delay: 1 }}
                // viewport={{ once: true }}
                />
                {[...Array(3)].map((_, index) => (
                    <motion.article
                        key={index}
                        className="max-w-[400px] flex flex-col"
                        initial="hidden"
                        whileInView="visible"
                        // viewport={{ once: true }}
                        variants={fadeInFrom("bottom", 0.5 + index * 0.3)}
                    >
                        <img
                            src={`/assets/A lot of documents with a frustrated lady${index ? ` (${index})` : ""}.svg`}
                            alt=""
                            className="w-full h-auto"
                        />
                        <div className="py-8">
                            <h4 className="text-[24px] fonr-semibold">
                                {[
                                    "Drop Your Masterpiece",
                                    "Pick Your Style (Guide)",
                                    "Witness the Citation Transformation",
                                ][index]}
                            </h4>
                            <p className="text-[18px] text-[#333333]">
                                {[
                                    "Just upload your document. No citation formatting required (we actually prefer it that way).",
                                    "APA, MLA, Chicago... or whatever formatting torture your professor prefers.",
                                    "We add perfect in-text citations and build your reference list faster than you can say 'bibliography.'",
                                ][index]}
                            </p>
                        </div>
                    </motion.article>
                ))}
            </div>
        </div>
    );
}
