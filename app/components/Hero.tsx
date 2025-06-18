"use client"

import React from 'react'
import Navbar from './Navbar'
import { motion } from 'framer-motion'
import Link from 'next/link'

type HeroProps = {
    setIsRegisterReady: (ready: boolean) => void;
};

const Hero: React.FC<HeroProps> = ({ setIsRegisterReady }) => {

    return (
        <>
            <div className='relative flex flex-col items-center justify-center rounded-b-[50px] border-b border-b-[#DEE5ED] bg-[#010F34] p-4 text-white shadow-xl sm:p-8'>
                <img src="/assets/Lights.png" alt="light" className='absolute left-0 top-0' />
                <img src="/assets/Lights (2).png" alt="light" className='absolute right-0 top-0' />
                <div className='relative flex flex-col items-center justify-center'>
                    <motion.div
                        initial={{ opacity: 0, y: -50 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                    >
                        <Navbar setIsRegisterReady={setIsRegisterReady} />
                        <div
                            className='flex max-w-[901px] flex-col items-center justify-center gap-4 pt-12 text-center'>
                            <div className='flex items-center gap-2 self-center rounded-full bg-white p-2 text-[#646464]'>
                                <img src="/assets/Images Container.png" alt="img" className='h-[26px] w-[56px]' />
                                <p>3,500+ Pro Users</p>
                            </div>
                            <div>
                                <h1 className="relative mt-[-1.00px] self-stretch text-center text-[40px] font-semibold leading-[1.2] tracking-normal [font-family:'Bricolage_Grotesque',Helvetica] md:text-[64px] ">One Upload. <br className='block sm:hidden' /> One Click. <br /> <span className='text-[#31DAC0]'>Perfect Citations.</span></h1>
                            </div>
                        </div>
                    </motion.div>
                    <img src="/assets/Vector.svg" alt="bg" className='absolute bottom-0' />
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                    >
                        <div className='flex flex-col items-center justify-center gap-8 pb-12'>
                            <p className="font-body-xlarge-medium leading-[var(--body-xlarge-medium-line-height)]w-full relative self-stretch text-center text-[length:var(--body-xlarge-medium-font-size)] font-[number:var(--body-xlarge-medium-font-weight)] tracking-[var(--body-xlarge-medium-letter-spacing)] text-foundation-whitewhite-500 sm:max-w-[901px]">Tweakrr automatically handles your in-text citations and reference lists. You write the brilliance, we&apos;ll handle the boring bits.</p>
                            <Link href="/dashboard" className=' z-50 rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-semibold text-[#010F34]'>
                                Cite It Right
                            </Link>
                        </div>
                    </motion.div>
                </div>
                <div className='relative flex flex-col sm:flex-row'>
                    <motion.div
                        className="relative"
                        initial={{ x: -100, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                    >
                        <motion.img
                            initial={{ rotate: -10, opacity: 0, x: -50 }}
                            whileInView={{ rotate: 0, opacity: 1, x: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            viewport={{ once: true, amount: 0.5 }}
                            src="/assets/a frazzled student surrounded by citation style guides.png"
                            alt=""
                            className="max-w-full sm:max-w-[280px] md:max-w-[526px]"
                        />
                        <img src="/assets/left-stroke.svg" alt="stroke" className='absolute left-0 top-[-4.5rem]' />
                    </motion.div>
                    <motion.div
                        className="relative mt-12 sm:mt-0"
                        initial={{ x: 100, opacity: 0 }}
                        whileInView={{ x: 0, opacity: 1 }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                    >
                        <img src="/assets/right stroke.svg" alt="stroke" className='absolute right-0 top-[-4.5rem]' />
                        <motion.img
                            initial={{ rotate: 10, opacity: 0, x: 50 }}
                            whileInView={{ rotate: 0, opacity: 1, x: 0 }}
                            transition={{ duration: 0.8, ease: "easeOut" }}
                            src="/assets/a relaxed student whose document magically gains perfect citations..png" alt=""
                            className="max-w-full sm:max-w-[280px] md:max-w-[526px]"
                        />
                        <img src="/assets/Frame 1707479763.png" alt="img"
                            className="absolute -right-24 bottom-0 hidden max-w-[150px] sm:block md:max-w-[220px]"
                        />
                    </motion.div>
                </div>
            </div >
        </>
    )
}

export default Hero
