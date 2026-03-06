import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI Studio — AI Video Generation",
  description:
    "Transform research papers, scripts, or existing videos into stunning AI-generated visuals in minutes.",
  keywords: ["AI video", "video generation", "script to video", "AI studio"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.variable} font-display antialiased bg-background-dark`}>
        {children}
      </body>
    </html>
  );
}
