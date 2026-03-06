"use client";

import { motion, AnimatePresence } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import VideoPlayer from "@/components/VideoPlayer";
import {
  ZoomIn, ZoomOut, Palette, Highlighter, Sparkles,
  Share2, Download, ChevronDown, Film, Clock, Layers,
  Scissors, Music2, Type, Sliders
} from "lucide-react";
import Link from "next/link";
import { useState, useRef } from "react";

const toolbarActions = [
  { icon: ZoomIn,       label: "Zoom In"     },
  { icon: ZoomOut,      label: "Zoom Out"    },
  { icon: Palette,      label: "Add Filter"  },
  { icon: Highlighter,  label: "Highlight"   },
  { icon: Scissors,     label: "Cut"         },
  { icon: Music2,       label: "Audio"       },
  { icon: Type,         label: "Caption"     },
  { icon: Sliders,      label: "Adjust"      },
];

const timelineClips = [
  { id: 1, label: "Scene 1",  color: "bg-primary/50",   width: "120px",  start: "0" },
  { id: 2, label: "Scene 2",  color: "bg-purple-500/50", width: "80px",  start: "120px" },
  { id: 3, label: "Scene 3",  color: "bg-emerald-500/50",width: "60px", start: "200px" },
  { id: 4, label: "Scene 4",  color: "bg-amber-500/50",  width: "100px", start: "260px" },
  { id: 5, label: "Scene 5",  color: "bg-pink-500/50",   width: "90px",  start: "360px" },
];

const menuItems = ["File", "Edit", "View", "History"];

export default function EditorPage() {
  const [activeFilter, setActiveFilter] = useState<string | null>(null);
  const [playheadPos, setPlayheadPos] = useState(35); // percent

  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="size-8 rounded-lg bg-primary/15 flex items-center justify-center text-primary">
            <Film size={16} />
          </div>
          <h2 className="text-sm font-semibold text-slate-300 truncate max-w-xs">
            Untitled Video — Cinematic Generation
          </h2>
        </div>

        <div className="flex items-center gap-6">
          {/* Menu items */}
          <nav className="hidden md:flex items-center gap-5">
            {menuItems.map((item) => (
              <motion.button
                key={item}
                whileHover={{ y: -1 }}
                className="text-xs font-medium text-slate-500 hover:text-slate-200 transition-colors"
              >
                {item}
              </motion.button>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="px-4 py-2 rounded-xl bg-white/[0.06] border border-white/[0.08] text-sm font-bold text-slate-300 hover:bg-white/10 transition-all flex items-center gap-1.5"
            >
              <Share2 size={13} />
              Share
            </motion.button>
            <Link href="/export">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                className="btn-primary text-sm flex items-center gap-1.5 py-2"
              >
                <Download size={13} />
                Export
              </motion.button>
            </Link>
            <div className="size-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-xs font-bold ml-1">
              A
            </div>
          </div>
        </div>
      </header>

      {/* ── Editor workspace ── */}
      <div className="flex-1 flex flex-col overflow-hidden p-5 gap-4 bg-[#0b0b1e]">

        {/* ── Video Player ── */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.21, 0.47, 0.32, 0.98] }}
          className="flex-1 min-h-0"
        >
          <VideoPlayer
            className="h-full w-full max-h-[420px]"
            poster={undefined}
          />
        </motion.div>

        {/* ── Toolbar / Quick Actions ── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.4 }}
          className="flex items-center justify-between gap-3"
        >
          <div className="flex items-center bg-white/[0.04] border border-white/[0.06] p-1 rounded-2xl gap-0.5 overflow-x-auto">
            {toolbarActions.map(({ icon: Icon, label }, i) => (
              <motion.button
                key={label}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                title={label}
                onClick={() => setActiveFilter(activeFilter === label ? null : label)}
                className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-medium transition-all whitespace-nowrap ${
                  activeFilter === label
                    ? "bg-primary/20 text-primary border border-primary/25"
                    : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.06]"
                }`}
              >
                <Icon size={14} />
                <span className="hidden sm:block">{label}</span>
              </motion.button>
            ))}
          </div>

          <motion.button
            whileHover={{ scale: 1.03, boxShadow: "0 0 30px rgba(17,17,212,0.4)" }}
            whileTap={{ scale: 0.97 }}
            className="btn-primary flex items-center gap-2 text-sm whitespace-nowrap flex-shrink-0"
          >
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
            >
              <Sparkles size={15} />
            </motion.div>
            Generate AI Scene
          </motion.button>
        </motion.div>

        {/* ── Timeline ── */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3, duration: 0.45 }}
          className="card p-4 space-y-3"
        >
          {/* Timeline header */}
          <div className="flex items-center justify-between text-[10px] text-slate-500 font-semibold uppercase tracking-widest">
            <span className="flex items-center gap-1.5">
              <Clock size={11} />
              Timeline Selection
            </span>
            <div className="flex items-center gap-4">
              <span>L: 00:12:05</span>
              <span className="text-primary">· · ·</span>
              <span>R: 01:45:22</span>
              <span className="text-amber-400 font-bold">DURATION 01:33:17</span>
            </div>
          </div>

          {/* Timeline track */}
          <div
            className="relative h-14 rounded-xl overflow-hidden bg-white/[0.03] timeline-track cursor-crosshair border border-white/[0.05]"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              setPlayheadPos(((e.clientX - rect.left) / rect.width) * 100);
            }}
          >
            {/* Waveform background */}
            <div className="absolute inset-0 flex items-center opacity-20">
              {Array.from({ length: 80 }).map((_, i) => (
                <div
                  key={i}
                  className="flex-1 bg-primary rounded-sm mx-px"
                  style={{ height: `${20 + Math.sin(i * 0.4) * 15 + Math.random() * 10}%` }}
                />
              ))}
            </div>

            {/* Scene clips */}
            <div className="absolute inset-0 flex items-center px-2 gap-1">
              {timelineClips.map((clip) => (
                <motion.div
                  key={clip.id}
                  whileHover={{ scaleY: 1.1 }}
                  className={`${clip.color} h-8 rounded-md border border-white/10 flex items-center justify-center cursor-pointer flex-shrink-0`}
                  style={{ width: clip.width }}
                  title={clip.label}
                >
                  <span className="text-[9px] text-white font-bold truncate px-1">{clip.label}</span>
                </motion.div>
              ))}
            </div>

            {/* Playhead */}
            <motion.div
              className="absolute top-0 bottom-0 flex flex-col items-center pointer-events-none"
              style={{ left: `${playheadPos}%` }}
              animate={{ left: `${playheadPos}%` }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            >
              <div className="w-px h-full bg-white/70" />
              <div className="-mt-1 size-3 rounded-full bg-white shadow-lg" />
            </motion.div>
          </div>

          {/* Timecode */}
          <div className="flex justify-between text-[10px] text-slate-600 font-mono">
            {["00:00", "00:30", "01:00", "01:30", "02:00", "02:30"].map((t) => (
              <span key={t}>{t}</span>
            ))}
          </div>
        </motion.div>
      </div>
    </AppLayout>
  );
}
