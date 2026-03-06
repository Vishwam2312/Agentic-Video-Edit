"use client";

import { motion } from "framer-motion";
import { Clock, MoreHorizontal, Play, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface ProjectCardProps {
  title: string;
  duration: string;
  resolution: string;
  thumbnail?: string;
  timeAgo: string;
  index?: number;
}

const gradients = [
  "from-blue-900/60 to-indigo-900/40",
  "from-purple-900/60 to-pink-900/40",
  "from-emerald-900/60 to-teal-900/40",
  "from-amber-900/60 to-orange-900/40",
];

export default function ProjectCard({
  title,
  duration,
  resolution,
  thumbnail,
  timeAgo,
  index = 0,
}: ProjectCardProps) {
  const [hovered, setHovered] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <motion.article
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.07, duration: 0.45, ease: [0.21, 0.47, 0.32, 0.98] }}
      whileHover={{ y: -4 }}
      onHoverStart={() => setHovered(true)}
      onHoverEnd={() => setHovered(false)}
      className="group relative cursor-pointer rounded-2xl overflow-hidden border border-white/[0.06] bg-surface-dark card-hover"
    >
      {/* ── Thumbnail ── */}
      <div className="relative aspect-video overflow-hidden bg-slate-900">
        {thumbnail ? (
          <motion.img
            src={thumbnail}
            alt={title}
            className="w-full h-full object-cover"
            animate={{ scale: hovered ? 1.06 : 1 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        ) : (
          <div
            className={cn(
              "w-full h-full bg-gradient-to-br",
              gradients[index % gradients.length]
            )}
          />
        )}

        {/* Overlay on hover */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: hovered ? 1 : 0 }}
          transition={{ duration: 0.25 }}
          className="absolute inset-0 bg-black/40 flex items-center justify-center"
        >
          <motion.div
            initial={{ scale: 0.7 }}
            animate={{ scale: hovered ? 1 : 0.7 }}
            transition={{ duration: 0.25 }}
            className="size-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30 flex items-center justify-center"
          >
            <Play size={18} className="text-white fill-white ml-0.5" />
          </motion.div>
        </motion.div>

        {/* Duration badge */}
        <div className="absolute top-2 right-2 bg-black/70 backdrop-blur-sm text-white text-[10px] font-bold px-2 py-0.5 rounded-md">
          {duration}
        </div>

        {/* Resolution badge */}
        <div className="absolute bottom-2 right-2 bg-primary/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-md">
          {resolution}
        </div>
      </div>

      {/* ── Info ── */}
      <div className="p-3.5">
        <div className="flex items-start justify-between gap-2">
          <h3 className="text-sm font-semibold text-slate-200 leading-tight group-hover:text-white transition-colors line-clamp-1">
            {title}
          </h3>
          <div className="relative">
            <button
              onClick={(e) => {
                e.stopPropagation();
                setMenuOpen(!menuOpen);
              }}
              className="p-1 rounded-lg hover:bg-white/10 text-slate-500 hover:text-slate-300 transition-colors flex-shrink-0"
            >
              <MoreHorizontal size={14} />
            </button>
            {menuOpen && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: -5 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                className="absolute right-0 top-7 z-50 bg-slate-800 border border-white/10 rounded-xl overflow-hidden shadow-xl min-w-[120px]"
              >
                <button className="flex items-center gap-2 w-full px-3 py-2 text-xs text-slate-300 hover:bg-white/10 transition-colors">
                  <Pencil size={12} /> Edit
                </button>
                <button className="flex items-center gap-2 w-full px-3 py-2 text-xs text-red-400 hover:bg-red-500/10 transition-colors">
                  <Trash2 size={12} /> Delete
                </button>
              </motion.div>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1.5 mt-1.5">
          <Clock size={11} className="text-slate-600" />
          <span className="text-[11px] text-slate-500">{timeAgo}</span>
        </div>
      </div>
    </motion.article>
  );
}
