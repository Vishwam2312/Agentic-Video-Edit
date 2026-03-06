"use client";

import { motion } from "framer-motion";
import { Clock, Pencil, Trash2, FileText, Eye } from "lucide-react";
import { cn } from "@/lib/utils";

interface SceneCardProps {
  sceneNumber: number;
  title: string;
  description: string;
  duration: string;
  tag?: string;
  thumbnail?: string;
  index?: number;
  onEdit?: () => void;
  onDelete?: () => void;
}

const tagColors: Record<string, string> = {
  INTRO:      "bg-blue-500/20 text-blue-400 border-blue-500/30",
  DETAIL:     "bg-purple-500/20 text-purple-400 border-purple-500/30",
  TRANSITION: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  OUTRO:      "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
};

export default function SceneCard({
  sceneNumber,
  title,
  description,
  duration,
  tag,
  thumbnail,
  index = 0,
  onEdit,
  onDelete,
}: SceneCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        delay: index * 0.08,
        duration: 0.5,
        ease: [0.21, 0.47, 0.32, 0.98],
      }}
      whileHover={{ y: -5, boxShadow: "0 20px 60px rgba(17,17,212,0.15)" }}
      className="group relative rounded-2xl overflow-hidden border border-white/[0.06] bg-surface-dark cursor-pointer transition-colors hover:border-primary/25"
    >
      {/* ── Thumbnail ── */}
      <div className="relative aspect-video bg-slate-900 overflow-hidden">
        {thumbnail ? (
          <motion.img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover"
            whileHover={{ scale: 1.06 }}
            transition={{ duration: 0.5 }}
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-slate-800 to-slate-900 flex items-center justify-center">
            <FileText size={32} className="text-slate-700" />
          </div>
        )}

        {/* Duration */}
        <div className="absolute top-2 left-2 bg-black/75 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-0.5 rounded-md flex items-center gap-1">
          <Clock size={9} />
          {duration}
        </div>

        {/* Scene number */}
        <div className="absolute top-2 right-2 size-6 rounded-full bg-primary/80 flex items-center justify-center text-white text-[10px] font-bold">
          {sceneNumber}
        </div>

        {/* Hover overlay */}
        <motion.div
          initial={{ opacity: 0 }}
          whileHover={{ opacity: 1 }}
          className="absolute inset-0 bg-black/50 flex items-center justify-center gap-2"
        >
          <button
            onClick={onEdit}
            className="size-9 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center text-white hover:bg-primary/60 transition-colors"
          >
            <Pencil size={14} />
          </button>
          <button className="size-9 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center text-white hover:bg-white/30 transition-colors">
            <Eye size={14} />
          </button>
          <button
            onClick={onDelete}
            className="size-9 rounded-xl bg-white/20 backdrop-blur-sm border border-white/30 flex items-center justify-center text-white hover:bg-red-500/60 transition-colors"
          >
            <Trash2 size={14} />
          </button>
        </motion.div>
      </div>

      {/* ── Content ── */}
      <div className="p-4">
        <div className="flex items-start justify-between gap-2 mb-2">
          <h3 className="text-sm font-bold text-slate-200 group-hover:text-white transition-colors leading-tight">
            {title}
          </h3>
          {tag && (
            <span
              className={cn(
                "badge border text-[9px] uppercase tracking-widest flex-shrink-0",
                tagColors[tag] ?? "bg-slate-700 text-slate-400"
              )}
            >
              {tag}
            </span>
          )}
        </div>
        <p className="text-[12px] text-slate-500 leading-relaxed line-clamp-2 italic">
          "{description}"
        </p>
      </div>

      {/* ── Footer Actions ── */}
      <div className="px-4 pb-4 flex items-center gap-2">
        <button
          onClick={onEdit}
          className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded-lg bg-white/[0.04] hover:bg-primary/10 hover:text-primary text-slate-400 text-xs font-medium transition-all border border-white/[0.05] hover:border-primary/20"
        >
          <FileText size={12} />
          Edit Script
        </button>
        <button className="size-8 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] flex items-center justify-center text-slate-400 hover:text-slate-200 transition-colors border border-white/[0.05]">
          <Pencil size={12} />
        </button>
      </div>
    </motion.div>
  );
}
