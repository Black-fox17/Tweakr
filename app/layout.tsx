import type { Metadata } from "next";
import { Lexend } from "next/font/google";
import "./globals.css";
import QueryProvider from "./QueryProvider";
import { Toaster } from "sonner";
import React from "react";
import NoScreenshotWrapper from "@/lib/NoScreenShot";
import { GoogleAnalytics } from "./components/GoogleAnalytics";
const lexend = Lexend({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-lexend',
});

export const metadata: Metadata = {
  title: "Tweakrr",
  description: "Seamless academic writing",
  icons: {
    icon: "/favicon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <link rel="icon" type="image/png" href="/favicon.png" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "Organization",
              "name": "Tweakrr",
              "url": "https://www.tweakrr.com",
              "logo": "https://www.tweakrr.com/favicon.png"
            }),
          }}
        />
      </head>
      <body className={`${lexend.variable} antialiased`}>
        <NoScreenshotWrapper>
          <QueryProvider>
            <Toaster position="top-right" richColors />
            <GoogleAnalytics />
            {children}
          </QueryProvider>
        </NoScreenshotWrapper>
      </body>
    </html>
  );
}
