"use client";

import { motion, AnimatePresence, Reorder } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import SceneCard from "@/components/SceneCard";
import {
  ArrowLeft, Search, Play, MoreVertical, Eye, ArrowUpDown,
  CheckCircle2, Volume2, Loader2
} from "lucide-react";
import Link from "next/link";
import { useState } from "react";

const initialScenes = [
  {
    id: "1",
    sceneNumber: 1,
    title: "Scene 1: The Awakening",
    description: "The laboratory hummed with electric energy. Suddenly, the central core pulsed with a deep indigo light…",
    duration: "0:08s",
    tag: "INTRO" as const,
  },
  {
    id: "2",
    sceneNumber: 2,
    title: "Scene 2: First Movement",
    description: "Metal fingers twitch. The hydraulic pistons hiss as the machine attempts its very first gesture towards autonomy…",
    duration: "0:12s",
    tag: "DETAIL" as const,
  },
  {
    id: "3",
    sceneNumber: 3,
    title: "Scene 3: Neural Bridge",
    description: "Flashes of code and synaptic connections spark across the screen, representing the transfer of consciousness.",
    duration: "0:05s",
    tag: "TRANSITION" as const,
  },
];

export default function ScenesPage() {
  const [scenes, setScenes] = useState(initialScenes);
  const [search, setSearch] = useState("");
  const [reorderMode, setReorderMode] = useState(false);

  const filtered = scenes.filter((s) =>
    s.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-3">
          <Link href="/dashboard">
            <motion.button
              whileHover={{ x: -2 }}
              whileTap={{ scale: 0.94 }}
              className="size-9 rounded-xl hover:bg-white/[0.06] flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors"
            >
              <ArrowLeft size={18} />
            </motion.button>
          </Link>
          <div className="h-4 w-px bg-white/[0.08]" />
          <div>
            <h2 className="text-sm font-bold text-white">The Future of AI Robotics</h2>
            <p className="text-[10px] text-slate-500">Draft · Last saved 2 mins ago</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={13} />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search scenes..."
              className="input-base pl-9 text-xs w-52"
            />
          </div>
          <Link href="/export">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="btn-primary flex items-center gap-2 text-xs py-2"
            >
              <Play size={13} className="fill-white" />
              Render Video
            </motion.button>
          </Link>
          <button className="size-9 rounded-xl border border-white/[0.08] flex items-center justify-center text-slate-500 hover:text-slate-300 hover:bg-white/[0.04] transition-colors">
            <MoreVertical size={15} />
          </button>
        </div>
      </header>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto p-6">

        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex items-end justify-between mb-6"
        >
          <div>
            <h1 className="text-2xl font-black text-white">Project Scenes</h1>
            <p className="text-slate-500 text-sm mt-0.5">Arrange and edit your cinematic sequences</p>
          </div>
          <div className="flex gap-2">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="btn-ghost flex items-center gap-2 text-xs py-2"
            >
              <Eye size={14} />
              Full Preview
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => setReorderMode(!reorderMode)}
              className={`flex items-center gap-2 text-xs py-2 px-4 rounded-xl border font-semibold transition-all ${
                reorderMode
                  ? "bg-primary/15 border-primary/30 text-primary"
                  : "btn-ghost"
              }`}
            >
              <ArrowUpDown size={14} />
              {reorderMode ? "Done" : "Reorder"}
            </motion.button>
          </div>
        </motion.div>

        {/* Scenes grid */}
        <AnimatePresence>
          {reorderMode ? (
            <Reorder.Group
              axis="y"
              values={scenes}
              onReorder={setScenes}
              className="space-y-3"
            >
              {scenes.map((scene, i) => (
                <Reorder.Item key={scene.id} value={scene}>
                  <motion.div
                    whileHover={{ scale: 1.01 }}
                    className="card p-4 flex items-center gap-4 cursor-grab active:cursor-grabbing"
                  >
                    <div className="size-8 rounded-lg bg-primary/15 flex items-center justify-center text-primary font-bold text-sm">
                      {scene.sceneNumber}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm font-semibold text-white">{scene.title}</p>
                      <p className="text-xs text-slate-500 truncate">{scene.description}</p>
                    </div>
                    <span className="text-xs text-slate-600">{scene.duration}</span>
                  </motion.div>
                </Reorder.Item>
              ))}
            </Reorder.Group>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5"
            >
              {filtered.map((scene, i) => (
                <SceneCard key={scene.id} {...scene} index={i} />
              ))}

              {/* Add scene card */}
              <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: filtered.length * 0.08, duration: 0.4 }}
                whileHover={{ y: -5, borderColor: "rgba(17,17,212,0.4)" }}
                className="group rounded-2xl border-2 border-dashed border-white/[0.06] hover:border-primary/30 aspect-video flex flex-col items-center justify-center gap-3 cursor-pointer transition-all"
              >
                <motion.div
                  whileHover={{ scale: 1.15, rotate: 5 }}
                  className="size-12 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center text-slate-600 text-2xl group-hover:bg-primary/10 group-hover:border-primary/20 group-hover:text-primary transition-all"
                >
                  +
                </motion.div>
                <div className="text-center">
                  <p className="text-sm font-semibold text-slate-500 group-hover:text-slate-300 transition-colors">
                    Add New Scene
                  </p>
                  <p className="text-[11px] text-slate-600">Insert after Scene {scenes.length}</p>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ── Footer status bar ── */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="mt-6 flex items-center justify-between py-3 px-4 rounded-xl bg-surface-dark border border-white/[0.05]"
        >
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1.5">
              <motion.span
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="size-2 rounded-full bg-emerald-400"
              />
              <span className="text-xs text-slate-400 font-medium">Ready for export</span>
            </div>
            <div className="flex items-center gap-1.5 text-slate-500">
              <Volume2 size={13} />
              <span className="text-xs">Audio levels normal</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex -space-x-1.5">
              {["A", "B"].map((letter) => (
                <div
                  key={letter}
                  className="size-6 rounded-full border-2 border-background-dark bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-[8px] font-bold"
                >
                  {letter}
                </div>
              ))}
              <div className="size-6 rounded-full border-2 border-background-dark bg-slate-700 flex items-center justify-center text-white text-[8px] font-bold">
                +2
              </div>
            </div>
            <span className="text-xs text-slate-600">Version 2.4</span>
          </div>
        </motion.div>
      </div>
    </AppLayout>
  );
}
