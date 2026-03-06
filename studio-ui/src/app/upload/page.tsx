"use client";

import { motion } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import UploadArea from "@/components/UploadArea";
import { Bell, Plus, FileText, Video, Image, BookOpen } from "lucide-react";

const stagger = {
  hidden: {},
  show: { transition: { staggerChildren: 0.08 } },
};
const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const recentFiles = [
  {
    name: "Cinematic_Intro.mp4",
    type: "mp4",
    size: "45.2 MB",
    duration: "0:45",
    icon: Video,
    iconColor: "text-purple-400",
    iconBg: "bg-purple-500/10",
  },
  {
    name: "Quantum_Physics_Abstract.pdf",
    type: "pdf",
    size: "2.1 MB",
    duration: null,
    icon: BookOpen,
    iconColor: "text-red-400",
    iconBg: "bg-red-500/10",
  },
  {
    name: "Space_Exploration_Script.txt",
    type: "txt",
    size: "18 KB",
    duration: null,
    icon: FileText,
    iconColor: "text-blue-400",
    iconBg: "bg-blue-500/10",
  },
];

const supportedTypes = [
  { label: "PDF",  desc: "Research papers, documents",   icon: BookOpen, color: "text-red-400",    bg: "bg-red-500/10" },
  { label: "TXT",  desc: "Scripts, plain text",            icon: FileText, color: "text-blue-400",  bg: "bg-blue-500/10" },
  { label: "MP4",  desc: "Reference videos, clips",        icon: Video,    color: "text-purple-400", bg: "bg-purple-500/10" },
  { label: "IMG",  desc: "Reference images, stills",       icon: Image,    color: "text-amber-400", bg: "bg-amber-500/10" },
];

export default function UploadPage() {
  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <h2 className="text-base font-semibold text-slate-200">Upload Assets</h2>
        <div className="flex items-center gap-3">
          <button className="size-9 rounded-xl hover:bg-white/[0.06] flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors">
            <Bell size={18} />
          </button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="btn-primary text-sm flex items-center gap-2 py-2.5"
          >
            <Plus size={15} />
            New Project
          </motion.button>
        </div>
      </header>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-8">

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45 }}
          >
            <h1 className="text-3xl font-black text-white mb-1">Create New Video</h1>
            <p className="text-slate-500 text-sm">
              Upload your source documents or media to start the AI generation process.
            </p>
          </motion.div>

          {/* Supported types */}
          <motion.div
            initial="hidden"
            animate="show"
            variants={stagger}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3"
          >
            {supportedTypes.map((t) => (
              <motion.div
                key={t.label}
                variants={fadeUp}
                whileHover={{ y: -3 }}
                className="card p-4 flex items-center gap-3 cursor-pointer hover:border-primary/20 transition-colors"
              >
                <div className={`size-9 rounded-xl ${t.bg} flex items-center justify-center`}>
                  <t.icon size={16} className={t.color} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-bold text-white">{t.label}</p>
                  <p className="text-[10px] text-slate-500 truncate">{t.desc}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>

          {/* Upload area */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.25, duration: 0.45 }}
          >
            <UploadArea />
          </motion.div>

          {/* File Preview Library */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.35, duration: 0.45 }}
            className="space-y-4"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                File Preview Library
              </h3>
              <button className="text-xs text-primary hover:text-primary-300 font-medium transition-colors">
                View all
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {recentFiles.map((file, i) => (
                <motion.div
                  key={file.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 + i * 0.07, duration: 0.4 }}
                  whileHover={{ y: -4, borderColor: "rgba(17,17,212,0.3)" }}
                  className="card p-4 cursor-pointer group transition-colors"
                >
                  <div className="aspect-video rounded-xl mb-3 overflow-hidden flex items-center justify-center bg-white/[0.03] border border-white/[0.05] relative group-hover:border-primary/20 transition-colors">
                    <file.icon size={28} className={`${file.iconColor} opacity-60`} />
                    {file.duration && (
                      <div className="absolute top-2 right-2 bg-black/70 text-white text-[10px] font-bold px-1.5 py-0.5 rounded">
                        {file.duration}
                      </div>
                    )}
                  </div>
                  <p className="text-xs font-semibold text-slate-300 truncate">{file.name}</p>
                  <p className="text-[10px] text-slate-600 mt-0.5">{file.size}</p>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </AppLayout>
  );
}
