"use client"

import FAQs from "./components/FAQs";
import Hero from "./components/Hero";
import { motion } from "framer-motion";
import HowItWorks from "./components/HowItWorks";
import Benefit from "./components/Benefit";
import TestimonialsSection from "./components/Testimonial";
import Footer from "./components/Footer";
import Pricing from "./components/Pricing";
import { useState } from "react";
import CreateAccountModal from "./components/CreateAccountModal";

export default function Home() {
  const [isPlaying, setIsPlaying] = useState(false)
  const [isRegisterReady, setIsRegisterReady] = useState<boolean>(false)
  const [isLogin, setIsLogin] = useState<boolean>(true)




  return (
    <div className="">
      {isRegisterReady && (
        <CreateAccountModal
          setIsRegisterReady={setIsRegisterReady}
          isLogin={isLogin}
          setIsLogin={setIsLogin}
        />
      )}
      <Hero setIsRegisterReady={setIsRegisterReady} />
      <div className="flex flex-col items-center justify-center gap-8 p-4 py-10 sm:p-8">
        <motion.p
          className="text-[24px] font-semibold"
          initial={{ y: -40, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
        // viewport={{ once: true, amount: 0.5 }}
        >
          When Citations Attack!
        </motion.p>
        {!isPlaying ? (
          <motion.img
            src="/assets/frustrated students trying to reference her work after long document processing.png"
            alt="video thumbnail"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            transition={{ duration: 1, ease: "easeOut" }}
            className="cursor-pointer"
            onClick={() => setIsPlaying(true)}
          />
        ) : (
          <div className="size-[25rem] sm:size-[27rem]">
            <motion.video
              src="/video/Tweakrradsvideo.mp4" // replace with your actual video path
              controls
              autoPlay
              className="size-full rounded-lg "
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.6, ease: "easeOut" }}
            />
          </div>
        )}

        <motion.p
          initial={{ y: 40, opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.7, ease: "easeOut" }}
          // viewport={{ once: true, amount: 0.5 }}
          className="text-center text-[16px] font-medium text-[#333333]">
          See how bad manual citations can be... and how Tweakrr makes them disappear forever.
        </motion.p>
      </div>
      <div className="flex flex-col items-center justify-center gap-4 py-12">
        <p className="text-center font-medium">Trusted by over 14,540 businesses to enhance learning and drive educational growth.</p>
        <motion.div
          className="flex w-max items-stretch space-x-8"
          animate={{ x: [100, -100] }} // Adjust based on content width
          transition={{
            repeat: Infinity,
            repeatType: "loop",
            ease: "linear",
            duration: 20,
          }}
        >
          <img src="/assets/Logo (5).png" alt="logo" />
          <img src="/assets/Logo (5).png" alt="logo" />
          <img src="/assets/Logo (4).png" alt="logo" />
          <img src="/assets/Logo (2).png" alt="logo" />
          <img src="/assets/Logo (1).png" alt="logo" />
          <img src="/assets/Logo.png" alt="logo" />
        </motion.div>
      </div>
      <HowItWorks />
      <Benefit />
      <TestimonialsSection />
      <Pricing setIsRegisterReady={setIsRegisterReady} />
      <FAQs />
      <Footer />
    </div>
  );
}
