"use client";

import { motion, useScroll, useTransform, AnimatePresence } from "framer-motion";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import {
  Sparkles, ArrowRight, Play, Zap, BookOpen, Mic2, CheckCircle2,
  Twitter, Star, Brain, Film, ChevronRight
} from "lucide-react";
import { useRef, useState } from "react";

/* ── Animation Variants ── */
const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease: [0.21, 0.47, 0.32, 0.98] } },
};

const stagger = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.1 } },
};

/* ── Features Data ── */
const features = [
  {
    icon: Film,
    title: "Script to Video",
    desc:  "Convert any raw text script into a fully choreographed and animated high-fidelity video automatically.",
    color: "from-blue-500/20 to-primary/10",
    border: "border-blue-500/20",
  },
  {
    icon: BookOpen,
    title: "Research Summary",
    desc:  "Turn complex academic journals and data-heavy whitepapers into engaging visual narratives for any audience.",
    color: "from-purple-500/20 to-pink-500/10",
    border: "border-purple-500/20",
  },
  {
    icon: Mic2,
    title: "AI Voiceovers",
    desc:  "Choose from a library of professional human-like voices in 50+ languages with emotional resonance control.",
    color: "from-emerald-500/20 to-teal-500/10",
    border: "border-emerald-500/20",
  },
  {
    icon: Brain,
    title: "Smart Scenes",
    desc:  "AI automatically segments your content into cinematic scenes with transitions and visual cues.",
    color: "from-amber-500/20 to-orange-500/10",
    border: "border-amber-500/20",
  },
];

/* ── Pricing ── */
const plans = [
  {
    name:  "Starter",
    price: "$0",
    period: "/month",
    desc:  "Perfect for experimentation",
    cta:   "Get Started",
    ctaStyle: "btn-ghost",
    popular: false,
    features: ["5 videos per month", "720p HD resolution", "Standard AI voices", "Basic export formats"],
  },
  {
    name:   "Professional",
    price:  "$49",
    period: "/month",
    desc:   "For serious creators",
    cta:    "Upgrade to Pro",
    ctaStyle: "btn-primary",
    popular: true,
    features: ["Unlimited video exports", "4K Ultra HD resolution", "Premium cloned voices", "No watermarks", "Priority rendering"],
  },
  {
    name:   "Enterprise",
    price:  "$199",
    period: "/month",
    desc:   "For teams & organizations",
    cta:    "Contact Sales",
    ctaStyle: "btn-ghost",
    popular: false,
    features: ["Custom AI models", "API & SDK access", "Dedicated support", "Team collaboration", "SLA guarantee"],
  },
];

/* ── Stats ── */
const stats = [
  { value: "50K+", label: "Videos Generated" },
  { value: "12K+", label: "Active Creators"  },
  { value: "99.2%", label: "Uptime SLA"      },
  { value: "4.9★", label: "User Rating"      },
];

/* ── Floating Particle ── */
function Particle({ x, y, delay }: { x: string; y: string; delay: number }) {
  return (
    <motion.div
      className="absolute size-1 rounded-full bg-primary/40"
      style={{ left: x, top: y }}
      animate={{
        y:       [0, -30, 0],
        opacity: [0.2, 0.8, 0.2],
        scale:   [1, 1.5, 1],
      }}
      transition={{ duration: 4 + delay, repeat: Infinity, delay, ease: "easeInOut" }}
    />
  );
}

/* ── Animated gradient orb ── */
function GlowOrb({ className }: { className?: string }) {
  return (
    <motion.div
      className={`absolute rounded-full blur-3xl pointer-events-none ${className}`}
      animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.5, 0.3] }}
      transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
    />
  );
}

export default function LandingPage() {
  const heroRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: heroRef });
  const heroY = useTransform(scrollYProgress, [0, 1], [0, -80]);
  const heroOpacity = useTransform(scrollYProgress, [0, 0.6], [1, 0]);
  const [demoPlaying, setDemoPlaying] = useState(false);

  const particles = [
    { x: "10%", y: "20%", delay: 0  },
    { x: "85%", y: "15%", delay: 1  },
    { x: "70%", y: "60%", delay: 2  },
    { x: "20%", y: "75%", delay: 0.5 },
    { x: "50%", y: "30%", delay: 1.8 },
    { x: "35%", y: "88%", delay: 0.7 },
    { x: "92%", y: "45%", delay: 2.5 },
    { x: "5%",  y: "55%", delay: 1.2 },
  ];

  return (
    <div className="relative flex flex-col min-h-screen bg-background-dark overflow-x-hidden">
      <Navbar />

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ HERO ━ */}
      <section
        ref={heroRef}
        className="relative min-h-screen flex items-center justify-center overflow-hidden pt-24"
      >
        {/* Background elements */}
        <GlowOrb className="size-[600px] bg-primary/15 -top-32 -left-32" />
        <GlowOrb className="size-[400px] bg-purple-500/10 bottom-0 right-0" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_60%,rgba(17,17,212,0.08)_0%,transparent_70%)]" />
        {/* Grid */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:60px_60px]" />

        {/* Particles */}
        {particles.map((p, i) => <Particle key={i} {...p} />)}

        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="relative z-10 max-w-7xl mx-auto px-6 lg:px-10 flex flex-col lg:flex-row items-center gap-16"
        >
          {/* ── Left column ── */}
          <motion.div
            variants={stagger}
            initial="hidden"
            animate="show"
            className="flex-1 flex flex-col gap-8 text-center lg:text-left"
          >
            {/* Pill badge */}
            <motion.div variants={fadeUp} className="flex justify-center lg:justify-start">
              <motion.span
                whileHover={{ scale: 1.05 }}
                className="inline-flex items-center gap-2 rounded-full bg-primary/10 border border-primary/20 px-4 py-1.5 text-xs font-bold text-primary"
              >
                <span className="relative flex size-2">
                  <motion.span
                    className="absolute inline-flex size-full rounded-full bg-primary opacity-75"
                    animate={{ scale: [1, 2, 1], opacity: [0.75, 0, 0.75] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  />
                  <span className="relative size-2 rounded-full bg-primary" />
                </span>
                Next Generation AI   ·   Now in Beta
                <ChevronRight size={12} />
              </motion.span>
            </motion.div>

            {/* Headline */}
            <motion.div variants={fadeUp} className="space-y-2">
              <h1 className="text-5xl md:text-6xl xl:text-7xl font-black leading-[1.05] tracking-tight text-white">
                AI Video{" "}
                <br />
                <span className="gradient-text">Generation</span>
                <br />
                Studio
              </h1>
            </motion.div>

            {/* Subtitle */}
            <motion.p
              variants={fadeUp}
              className="text-slate-400 text-lg md:text-xl leading-relaxed max-w-[520px] mx-auto lg:mx-0"
            >
              Transform research papers, scripts, or existing videos into stunning,
              explainable AI-generated visuals in{" "}
              <span className="text-white font-semibold">minutes</span>.
            </motion.p>

            {/* CTAs */}
            <motion.div
              variants={fadeUp}
              className="flex flex-wrap gap-3 justify-center lg:justify-start"
            >
              <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}>
                <Link href="/dashboard" className="btn-primary flex items-center gap-2 text-base">
                  Start Project
                  <ArrowRight size={16} />
                </Link>
              </motion.div>
              <motion.button
                whileHover={{ scale: 1.04 }}
                whileTap={{ scale: 0.96 }}
                onClick={() => setDemoPlaying(true)}
                className="btn-ghost flex items-center gap-2 text-base"
              >
                <Play size={16} className="fill-current" />
                Watch Demo
              </motion.button>
            </motion.div>

            {/* Social proof */}
            <motion.div
              variants={fadeUp}
              className="flex items-center gap-4 justify-center lg:justify-start"
            >
              <div className="flex -space-x-2">
                {[0, 1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="size-8 rounded-full border-2 border-background-dark bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-[10px] font-bold"
                  >
                    {["A", "B", "C", "D"][i]}
                  </div>
                ))}
              </div>
              <div className="text-sm text-slate-400">
                <span className="text-white font-semibold">12,000+</span> creators already using AI Studio
              </div>
            </motion.div>
          </motion.div>

          {/* ── Right column — Video preview ── */}
          <motion.div
            initial={{ opacity: 0, x: 40, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.3, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="flex-1 w-full max-w-[580px]"
          >
            <motion.div
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              className="relative rounded-2xl overflow-hidden border border-white/[0.08] shadow-[0_0_80px_rgba(17,17,212,0.2)] aspect-video bg-slate-950"
            >
              {/* Mock video frame */}
              <div
                className="absolute inset-0 bg-cover bg-center opacity-70"
                style={{
                  backgroundImage:
                    "linear-gradient(135deg, #0a0a25 0%, #1a1250 40%, #0d0d30 100%)",
                }}
              />
              {/* Animated wave */}
              <svg
                className="absolute inset-0 w-full h-full opacity-30"
                viewBox="0 0 800 450"
                preserveAspectRatio="none"
              >
                <motion.path
                  d="M0,225 C100,150 200,300 300,225 S500,150 600,225 S700,300 800,225 L800,450 L0,450 Z"
                  fill="rgba(17,17,212,0.3)"
                  animate={{
                    d: [
                      "M0,225 C100,150 200,300 300,225 S500,150 600,225 S700,300 800,225 L800,450 L0,450 Z",
                      "M0,200 C100,280 200,140 300,200 S500,280 600,200 S700,140 800,200 L800,450 L0,450 Z",
                      "M0,225 C100,150 200,300 300,225 S500,150 600,225 S700,300 800,225 L800,450 L0,450 Z",
                    ],
                  }}
                  transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                />
              </svg>

              {/* Play button */}
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.button
                  whileHover={{ scale: 1.12 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setDemoPlaying(true)}
                  className="size-16 rounded-full bg-white/15 backdrop-blur-xl border border-white/25 flex items-center justify-center shadow-2xl"
                >
                  <Play size={24} className="fill-white text-white ml-1" />
                </motion.button>
              </div>

              {/* Corner badge */}
              <div className="absolute top-3 right-3 bg-primary/90 backdrop-blur-sm text-white text-[10px] font-bold px-2.5 py-1 rounded-lg">
                4K
              </div>

              {/* Generating overlay */}
              <motion.div
                className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-black/80 to-transparent"
              >
                <div className="flex items-center gap-2 mb-2">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                  >
                    <Sparkles size={12} className="text-primary" />
                  </motion.div>
                  <span className="text-xs text-slate-300 font-medium">Generating AI scenes...</span>
                </div>
                <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-primary to-purple-500 rounded-full"
                    animate={{ width: ["0%", "75%"] }}
                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                  />
                </div>
              </motion.div>
            </motion.div>

            {/* Floating cards */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.9, duration: 0.5 }}
              className="absolute -left-8 top-1/3 bg-surface-dark border border-white/[0.08] rounded-xl p-3 shadow-xl hidden lg:flex items-center gap-2.5"
            >
              <div className="size-8 rounded-lg bg-emerald-500/20 flex items-center justify-center">
                <CheckCircle2 size={16} className="text-emerald-400" />
              </div>
              <div>
                <p className="text-[11px] font-bold text-white">Scene rendered</p>
                <p className="text-[10px] text-slate-500">0.3s · 4K quality</p>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Scroll indicator */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2"
        >
          <span className="text-xs text-slate-600 font-medium">Scroll to explore</span>
          <motion.div
            animate={{ y: [0, 8, 0] }}
            transition={{ duration: 1.5, repeat: Infinity }}
            className="size-6 rounded-full border border-white/10 flex items-center justify-center"
          >
            <div className="size-1.5 rounded-full bg-slate-500" />
          </motion.div>
        </motion.div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ STATS ━ */}
      <section className="relative py-16 border-y border-white/[0.05]">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_50%,rgba(17,17,212,0.05)_0%,transparent_70%)]" />
        <motion.div
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-80px" }}
          variants={stagger}
          className="max-w-7xl mx-auto px-6 lg:px-10 grid grid-cols-2 md:grid-cols-4 gap-8"
        >
          {stats.map(({ value, label }) => (
            <motion.div key={label} variants={fadeUp} className="text-center">
              <p className="text-4xl font-black gradient-text mb-1">{value}</p>
              <p className="text-sm text-slate-500 font-medium">{label}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ FEATURES ━ */}
      <section id="features" className="py-28 px-6 lg:px-10">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="text-center mb-16"
          >
            <motion.div variants={fadeUp} className="flex justify-center mb-4">
              <span className="badge bg-primary/10 border border-primary/20 text-primary px-4 py-1.5">
                <Zap size={12} /> Powered by Advanced AI
              </span>
            </motion.div>
            <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-black text-white mb-4">
              Everything you need to create
              <br />
              <span className="gradient-text">stunning AI videos</span>
            </motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400 text-lg max-w-xl mx-auto">
              Engineered for creators who value speed and quality. Our suite of AI tools
              streamlines the entire video production pipeline.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="grid grid-cols-1 md:grid-cols-2 gap-5"
          >
            {features.map((feat, i) => (
              <motion.div
                key={feat.title}
                variants={{
                  hidden: { opacity: 0, y: 32, scale: 0.96 },
                  show:   { opacity: 1, y: 0, scale: 1, transition: { delay: i * 0.08, duration: 0.5 } },
                }}
                whileHover={{ y: -6, boxShadow: "0 20px 60px rgba(17,17,212,0.12)" }}
                className={`relative rounded-2xl p-6 border ${feat.border} bg-gradient-to-br ${feat.color} backdrop-blur-sm overflow-hidden card-hover cursor-pointer`}
              >
                <motion.div
                  whileHover={{ scale: 1.1, rotate: 5 }}
                  className="size-12 rounded-2xl bg-white/[0.06] border border-white/[0.08] flex items-center justify-center mb-4"
                >
                  <feat.icon size={22} className="text-slate-300" />
                </motion.div>
                <h3 className="text-white font-bold text-lg mb-2">{feat.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>

                {/* Corner decoration */}
                <div className="absolute -right-6 -bottom-6 size-24 rounded-full bg-white/[0.02] border border-white/[0.04]" />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ PRICING ━ */}
      <section id="pricing" className="py-28 px-6 lg:px-10">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="text-center mb-16"
          >
            <motion.h2 variants={fadeUp} className="text-4xl md:text-5xl font-black text-white mb-4">
              Choose your plan
            </motion.h2>
            <motion.p variants={fadeUp} className="text-slate-400 text-lg">
              Scale your creativity with our flexible pricing models.
            </motion.p>
          </motion.div>

          <motion.div
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-80px" }}
            variants={stagger}
            className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch"
          >
            {plans.map((plan, i) => (
              <motion.div
                key={plan.name}
                variants={{
                  hidden: { opacity: 0, y: 40 },
                  show: {
                    opacity: 1, y: 0,
                    transition: { delay: i * 0.1, duration: 0.5, ease: [0.21, 0.47, 0.32, 0.98] },
                  },
                }}
                whileHover={{ y: -6 }}
                className={`relative rounded-3xl p-7 flex flex-col gap-5 transition-all ${
                  plan.popular
                    ? "bg-gradient-to-b from-primary/20 to-primary/5 border-2 border-primary/40 shadow-[0_0_60px_rgba(17,17,212,0.2)]"
                    : "bg-surface-dark border border-white/[0.06]"
                }`}
              >
                {plan.popular && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary text-white text-[10px] font-black uppercase tracking-widest px-4 py-1.5 rounded-full shadow-lg"
                  >
                    Most Popular
                  </motion.div>
                )}

                <div>
                  <h3 className="text-white font-bold text-lg mb-1">{plan.name}</h3>
                  <p className="text-slate-500 text-sm">{plan.desc}</p>
                </div>

                <div className="flex items-end gap-1">
                  <span className="text-5xl font-black text-white">{plan.price}</span>
                  <span className="text-slate-500 mb-1.5 text-sm">{plan.period}</span>
                </div>

                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.97 }}
                  className={plan.ctaStyle === "btn-primary" ? "btn-primary text-center" : "btn-ghost text-center"}
                >
                  {plan.cta}
                </motion.button>

                <ul className="space-y-2.5">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-center gap-2.5 text-sm text-slate-400">
                      <CheckCircle2 size={14} className={plan.popular ? "text-primary" : "text-slate-600"} />
                      {f}
                    </li>
                  ))}
                </ul>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ CTA BANNER ━ */}
      <section className="py-28 px-6 lg:px-10">
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="max-w-5xl mx-auto relative rounded-3xl overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-br from-primary via-indigo-600 to-purple-700" />
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_50%,rgba(255,255,255,0.1)_0%,transparent_60%)]" />
          {/* Noise */}
          <div className="absolute inset-0 opacity-[0.03] bg-[url('data:image/svg+xml,%3Csvg viewBox=%220 0 256 256%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cfilter id=%22noise%22%3E%3CfeTurbulence type=%22fractalNoise%22 baseFrequency=%220.9%22 numOctaves=%224%22 stitchTiles=%22stitch%22/%3E%3C/filter%3E%3Crect width=%22100%25%22 height=%22100%25%22 filter=%22url(%23noise)%22/%3E%3C/svg%3E')]" />

          <div className="relative z-10 flex flex-col items-center text-center py-20 px-8 gap-6">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Sparkles size={40} className="text-white/60" />
            </motion.div>
            <h2 className="text-4xl md:text-5xl font-black text-white leading-tight max-w-2xl">
              Ready to revolutionize your video workflow?
            </h2>
            <p className="text-white/70 text-lg max-w-lg">
              Join thousands of researchers and creators using AI to tell better stories.
            </p>
            <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.96 }}>
              <Link
                href="/dashboard"
                className="bg-white text-primary font-black px-8 py-4 rounded-2xl text-base shadow-2xl hover:shadow-white/20 transition-all"
              >
                Start Your Project →
              </Link>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ FOOTER ━ */}
      <footer className="border-t border-white/[0.06] py-10 px-6 lg:px-10">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2.5">
            <div className="size-7 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles size={13} className="text-white" />
            </div>
            <span className="text-white font-bold text-sm">AI Studio</span>
          </div>
          <div className="flex items-center gap-6 text-sm text-slate-500">
            <a href="#" className="hover:text-slate-300 transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Terms of Service</a>
            <a href="#" className="hover:text-slate-300 transition-colors">Contact</a>
          </div>
          <div className="flex items-center gap-3">
            <button className="size-8 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center text-slate-500 hover:text-white transition-colors">
              <Twitter size={14} />
            </button>
            <span className="text-slate-600 text-xs">© 2026 AI Video Generation Studio</span>
          </div>
        </div>
      </footer>

      {/* ── Demo modal ── */}
      <AnimatePresence>
        {demoPlaying && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-6"
            onClick={() => setDemoPlaying(false)}
          >
            <motion.div
              initial={{ scale: 0.85, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.85, opacity: 0 }}
              transition={{ type: "spring", duration: 0.4 }}
              className="w-full max-w-4xl bg-surface-dark border border-white/[0.08] rounded-3xl overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="aspect-video bg-gradient-to-br from-slate-900 to-black flex items-center justify-center">
                <span className="text-slate-600 font-medium">Demo video placeholder</span>
              </div>
              <div className="p-4 flex justify-end">
                <button
                  onClick={() => setDemoPlaying(false)}
                  className="btn-ghost text-sm px-4 py-2"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
