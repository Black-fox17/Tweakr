"use client"

import React, { useState, useEffect, useRef } from 'react';
import { Menu, X } from 'lucide-react'; // Icons, optional
import { motion, AnimatePresence } from 'framer-motion';



const Navbar = ({ setIsRegisterReady }: { setIsRegisterReady: (ready: boolean) => void }) => {
    const [isOpen, setIsOpen] = useState(false);
    const [active, setActive] = useState('App');
    const navbarRef = useRef<HTMLElement>(null);

    const navLinks = [
        { label: 'App', id: 'app' },
        { label: 'Benefits', id: 'benefits' },
        { label: 'Pricing', id: 'pricing' },
        { label: 'About', id: 'about' },
    ];

    // Handle click outside to close dropdown
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (navbarRef.current && !navbarRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        // Only add event listener when dropdown is open
        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [isOpen]);



    return (
        <nav
            ref={navbarRef}
            className='relative flex w-full items-center justify-between rounded-full border border-[#343F5D] p-2 sm:w-[720px]'>
            <img src="/assets/Coloured.png" alt="logo" className='h-[40px] w-[129px]' />

            <div className="px-4 sm:hidden">
                <button onClick={() => setIsOpen(!isOpen)}>
                    {isOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </div>

            <ul className="hidden items-center justify-center gap-4 font-semibold text-[#828282] sm:flex">
                {navLinks.map(({ label, id }) => (
                    <li
                        key={id}
                        onClick={() => {
                            setActive(label);
                            setIsOpen(false);
                            document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className={`cursor-pointer rounded-full transition-all  ${active === label ? ' bg-[#555E77] px-[18px] py-[10px] text-white' : ''
                            }`}>
                        {label}
                    </li>
                ))}
            </ul>


            <button
                onClick={() => setIsRegisterReady(true)}
                className='hidden rounded-full bg-[#31DAC0] px-[20px] py-[14px] font-semibold text-[#010F34] sm:block'>
                Login
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -10 }}
                        transition={{ duration: 0.3 }}
                        className="absolute left-0 top-full z-50 mt-2 flex w-full flex-col gap-4 rounded-xl bg-[#010F34] p-4 sm:hidden">
                        <ul className="flex flex-col gap-2 font-semibold text-[#828282]">
                            {navLinks.map(({ label, id }) => (
                                <li
                                    key={id}
                                    onClick={() => {
                                        setActive(label);
                                        setIsOpen(false);
                                        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
                                    }}
                                    className={`cursor-pointer rounded-full px-4 py-2 transition-all ${active === label ? 'bg-[#555E77] text-white' : ''
                                        }`}
                                >
                                    {label}
                                </li>
                            ))}
                        </ul>
                        <button
                            onClick={() => setIsRegisterReady(true)}
                            className="w-full rounded-full bg-[#31DAC0] px-6 py-3 font-semibold text-[#010F34]"
                        >
                            Login
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </nav>
    )
}

export default Navbar
