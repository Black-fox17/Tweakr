import React from 'react';
import { motion } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

const Footer = () => {
    return (
        <div className="flex items-center justify-center bg-white px-4 py-10">
            <div className="flex w-full max-w-[1200px] flex-col items-center gap-8 sm:items-start">
                {/* Top Header Section */}
                <div className="flex w-full flex-col gap-6 md:flex-row">
                    <motion.h1
                        initial={{ x: -100, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        transition={{ duration: 0.6 }}
                        // viewport={{ once: true, amount: 0.3 }}
                        className="text-center text-[32px] font-semibold sm:text-[40px] md:w-[55%] md:text-left md:text-[60px]"
                    >
                        Start Your Hassle-Free Referencing Now!
                    </motion.h1>

                    <div className="flex w-full flex-col items-center justify-between gap-4 md:w-[45%] md:items-end md:gap-8">
                        <motion.p
                            initial={{ y: -100, opacity: 0 }}
                            whileInView={{ y: 0, opacity: 1 }}
                            transition={{ duration: 0.6 }}
                            // viewport={{ once: true, amount: 0.3 }}
                            className="px-4 text-center text-[16px] sm:text-[18px] md:px-0"
                        >
                            Avoid citation errors and formatting struggles—let Tweakrr handle your references in one click.
                        </motion.p>
                        <motion.button
                            initial={{ y: 100, opacity: 0 }}
                            whileInView={{ y: 0, opacity: 1 }}
                            transition={{ duration: 0.6, delay: 0.2 }}
                        // viewport={{ once: true, amount: 0.3 }}
                        >
                            <Link href="/dashboard" className="flex w-fit gap-2 rounded-full bg-[#31DAC0] px-5 py-3 text-center text-[16px] font-semibold text-white sm:text-[17px]"
                            >
                                Reference Your Document Today
                                <ArrowRight />
                            </Link>
                        </motion.button>
                    </div>
                </div>

                {/* Bottom Info Section */}
                <div className="flex w-full flex-col gap-6 lg:flex-row">
                    {/* Image */}
                    <motion.div
                        initial={{ y: 50, opacity: 0 }}
                        whileInView={{ y: 0, opacity: 1 }}
                        transition={{ duration: 0.6, delay: 0.3 }}
                        // viewport={{ once: true, amount: 0.3 }}
                        className="h-auto w-full sm:h-[265px] lg:w-2/5"
                    >
                        <img
                            src="/assets/Frame 1707479715.png"
                            alt="tweakrr"
                            className="object-fit size-full rounded-xl"
                        />
                    </motion.div>

                    {/* Links */}
                    <motion.div
                        initial={{ y: 50, opacity: 0 }}
                        whileInView={{ y: 0, opacity: 1 }}
                        transition={{ duration: 0.6, delay: 0.5 }}
                        // viewport={{ once: true, amount: 0.3 }}
                        className="flex w-full flex-row flex-wrap items-center justify-between gap-6 whitespace-nowrap rounded-[24px] bg-[#EDEDED] p-6 sm:p-10 lg:w-3/5"
                    >
                        <div className="flex flex-col gap-4">
                            <p className="font-bold">Legal</p>
                            <ul className="flex flex-col gap-3 font-medium">
                                <li><Link href={"privacypolicy"}>Privacy Policy</Link></li>
                                <li> <Link href={"/termanscondition"}> Terms of Use</Link></li>
                                {/* <li>License</li> */}
                            </ul>
                        </div>
                        <div className="flex flex-col gap-4">
                            <p className="font-bold">Company</p>
                            <ul className="flex flex-col gap-3 font-medium">
                                {/* <li>About Us</li> */}
                                <li>Contact<br /><span>+2347062561696</span> <br /><span className='text-sm'>tweakr01@gmail.com</span><br /><span className=''>Oluwatedo,Zone 2, Akogi Street, Oloko, Apata, Ibadan</span></li>
                                <li>Support</li>
                            </ul>
                        </div>
                        <div className="flex flex-col gap-4">
                            <p className="font-bold">Social</p>
                            <ul className="flex flex-col gap-3 font-medium">
                                <li><Link href={"https://x.com/tweakrrAI?t=NHAE3A71D5PMcnx9vNFWMg&s=09"}>X</Link></li>
                                <li><Link href={"https://www.instagram.com/tweakrrai?igsh=MXBreGN2dmhtNzM2aw=="}>Instagram</Link></li>
                                <li><Link href={"https://www.linkedin.com/company/tweakrr-company/posts/?feedView=all"}>LinkedIn</Link></li>
                            </ul>
                        </div>
                    </motion.div>
                </div>
            </div>
        </div >
    );
};

export default Footer;
