"use client";

import Link from "next/link";
import { motion, useScroll, useTransform } from "framer-motion";
import { Sparkles, Menu, X } from "lucide-react";
import { useState, useEffect } from "react";

const navLinks = [
  { href: "#features", label: "Features" },
  { href: "#pricing",  label: "Pricing"  },
  { href: "#demo",     label: "Demo"     },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const { scrollY } = useScroll();
  const bgOpacity = useTransform(scrollY, [0, 80], [0, 1]);

  useEffect(() => {
    const unsub = scrollY.on("change", (v) => setScrolled(v > 30));
    return unsub;
  }, [scrollY]);

  return (
    <motion.header
      style={{ "--bg-opacity": bgOpacity } as React.CSSProperties}
      className="fixed top-0 inset-x-0 z-50 px-6 md:px-10 lg:px-20 py-4"
    >
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5, ease: "easeOut" }}
        className={`mx-auto max-w-7xl flex items-center justify-between rounded-2xl px-5 py-3 transition-all duration-300 ${
          scrolled
            ? "bg-[#0d0d1e]/90 backdrop-blur-xl border border-white/[0.07] shadow-2xl"
            : ""
        }`}
      >
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <motion.div
            whileHover={{ rotate: 10, scale: 1.05 }}
            className="size-9 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/40"
          >
            <Sparkles size={17} className="text-white" />
          </motion.div>
          <span className="text-white font-bold text-lg tracking-tight">AI Studio</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => (
            <motion.a
              key={link.href}
              href={link.href}
              whileHover={{ y: -1 }}
              className="text-slate-400 hover:text-white text-sm font-medium transition-colors"
            >
              {link.label}
            </motion.a>
          ))}
        </nav>

        {/* CTA buttons */}
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="hidden md:block text-slate-400 hover:text-white text-sm font-medium transition-colors"
          >
            Login
          </Link>
          <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}>
            <Link
              href="/dashboard"
              className="bg-primary hover:bg-primary-600 text-white text-sm font-bold px-5 py-2.5 rounded-xl shadow-lg shadow-primary/30 transition-all duration-200"
            >
              Get Started
            </Link>
          </motion.div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden text-slate-400 hover:text-white p-1"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            {menuOpen ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </motion.div>

      {/* Mobile menu */}
      {menuOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="md:hidden mt-2 mx-auto max-w-7xl bg-[#0d0d1e]/95 backdrop-blur-xl border border-white/[0.07] rounded-2xl p-4 space-y-1"
        >
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="block px-4 py-2.5 text-slate-300 hover:text-white hover:bg-white/[0.04] rounded-xl text-sm font-medium transition-colors"
              onClick={() => setMenuOpen(false)}
            >
              {link.label}
            </a>
          ))}
          <Link
            href="/dashboard"
            className="block mt-2 text-center bg-primary text-white font-bold py-2.5 rounded-xl"
            onClick={() => setMenuOpen(false)}
          >
            Get Started
          </Link>
        </motion.div>
      )}
    </motion.header>
  );
}
