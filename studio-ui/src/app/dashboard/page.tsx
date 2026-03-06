"use client";

import { motion, AnimatePresence } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import ProjectCard from "@/components/ProjectCard";
import {
  Search, Bell, Settings, TrendingUp, Clock, Video,
  Plus, SlidersHorizontal, LayoutGrid, List
} from "lucide-react";
import { useState } from "react";

const stagger = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.06 } },
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const projects = [
  { title: "Cinematic Nature",      duration: "0:30", resolution: "4K",    timeAgo: "2h ago" },
  { title: "Product Promo v2",      duration: "0:15", resolution: "1080p", timeAgo: "5h ago" },
  { title: "Character Interview",   duration: "1:00", resolution: "4K",    timeAgo: "1d ago" },
  { title: "Social Media Clip",     duration: "0:10", resolution: "1080p", timeAgo: "3d ago" },
  { title: "AI Explainer Series",   duration: "2:15", resolution: "4K",    timeAgo: "5d ago" },
  { title: "Brand Story Reel",      duration: "0:45", resolution: "1080p", timeAgo: "1w ago" },
];

const tabs = ["All", "Recent", "Drafts"] as const;

const stats = [
  { icon: Video,      label: "Total Projects",  value: "24",     change: "+3 this week",   color: "text-blue-400",    bg: "bg-blue-500/10" },
  { icon: Clock,      label: "Render Hours",    value: "14.5h",  change: "+2.1h today",     color: "text-purple-400",  bg: "bg-purple-500/10" },
  { icon: TrendingUp, label: "Videos Exported", value: "18",     change: "+5 this month",   color: "text-emerald-400", bg: "bg-emerald-500/10" },
];

export default function DashboardPage() {
  const [search, setSearch] = useState("");
  const [activeTab, setActiveTab] = useState<typeof tabs[number]>("All");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const filtered = projects.filter((p) =>
    p.title.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <div className="relative w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={15} />
          <input
            type="text"
            placeholder="Search projects..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-base w-full pl-9 text-sm bg-white/[0.04]"
          />
        </div>
        <div className="flex items-center gap-3">
          <motion.button whileTap={{ scale: 0.9 }} className="size-9 rounded-xl hover:bg-white/[0.06] flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors relative">
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 size-2 rounded-full bg-primary" />
          </motion.button>
          <motion.button whileTap={{ scale: 0.9 }} className="size-9 rounded-xl hover:bg-white/[0.06] flex items-center justify-center text-slate-500 hover:text-slate-300 transition-colors">
            <Settings size={18} />
          </motion.button>
          <div className="size-9 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white text-sm font-bold cursor-pointer">
            A
          </div>
        </div>
      </header>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">

        {/* Stats Row */}
        <motion.div
          initial="hidden"
          animate="show"
          variants={stagger}
          className="grid grid-cols-1 sm:grid-cols-3 gap-4"
        >
          {stats.map((stat) => (
            <motion.div
              key={stat.label}
              variants={fadeUp}
              whileHover={{ y: -3 }}
              className="card p-5 flex items-center gap-4"
            >
              <div className={`size-11 rounded-xl ${stat.bg} flex items-center justify-center flex-shrink-0`}>
                <stat.icon size={20} className={stat.color} />
              </div>
              <div>
                <p className="text-2xl font-black text-white">{stat.value}</p>
                <p className="text-xs text-slate-500 font-medium">{stat.label}</p>
                <p className="text-[11px] text-emerald-400 font-medium mt-0.5">{stat.change}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* ── Project grid header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-black text-white">Projects</h2>
            <p className="text-slate-500 text-sm mt-0.5">Manage and organize your AI generated videos</p>
          </div>

          <div className="flex items-center gap-2">
            {/* Tabs */}
            <div className="flex items-center gap-1 bg-white/[0.04] rounded-xl p-1 border border-white/[0.05]">
              {tabs.map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`relative px-4 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    activeTab === tab ? "text-white" : "text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {activeTab === tab && (
                    <motion.div
                      layoutId="tab-indicator"
                      className="absolute inset-0 bg-primary/20 border border-primary/30 rounded-lg"
                      transition={{ type: "spring", duration: 0.3 }}
                    />
                  )}
                  <span className="relative z-10">{tab}</span>
                </button>
              ))}
            </div>

            <button className="size-9 rounded-xl border border-white/[0.08] flex items-center justify-center text-slate-500 hover:text-slate-300 hover:bg-white/[0.04] transition-colors">
              <SlidersHorizontal size={15} />
            </button>
            <button
              onClick={() => setViewMode(viewMode === "grid" ? "list" : "grid")}
              className="size-9 rounded-xl border border-white/[0.08] flex items-center justify-center text-slate-500 hover:text-slate-300 hover:bg-white/[0.04] transition-colors"
            >
              {viewMode === "grid" ? <List size={15} /> : <LayoutGrid size={15} />}
            </button>
          </div>
        </div>

        {/* ── Grid ── */}
        <AnimatePresence mode="wait">
          <motion.div
            key={viewMode + activeTab}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className={`grid gap-4 ${viewMode === "grid" ? "grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4" : "grid-cols-1"}`}
          >
            {filtered.map((proj, i) => (
              <ProjectCard key={proj.title} {...proj} index={i} />
            ))}

            {/* ── New Project card ── */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: filtered.length * 0.07, duration: 0.4 }}
              whileHover={{ y: -4, borderColor: "rgba(17,17,212,0.4)" }}
              className="group rounded-2xl border-2 border-dashed border-white/[0.07] hover:border-primary/30 aspect-video flex flex-col items-center justify-center gap-3 cursor-pointer transition-all"
            >
              <motion.div
                whileHover={{ scale: 1.12, rotate: 5 }}
                className="size-12 rounded-2xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center group-hover:bg-primary/10 group-hover:border-primary/20 transition-all"
              >
                <Plus size={22} className="text-slate-500 group-hover:text-primary transition-colors" />
              </motion.div>
              <p className="text-sm font-medium text-slate-500 group-hover:text-slate-300 transition-colors">
                New Project
              </p>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      </div>
    </AppLayout>
  );
}
