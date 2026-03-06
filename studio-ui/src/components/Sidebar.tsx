"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Upload,
  FileText,
  Film,
  Video,
  Download,
  Settings,
  Sparkles,
  Plus,
  ChevronUp,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";

const navItems = [
  { href: "/dashboard", label: "Dashboard",    icon: LayoutDashboard },
  { href: "/upload",    label: "Upload",        icon: Upload },
  { href: "/scripts",   label: "Scripts",       icon: FileText },
  { href: "/scenes",    label: "Scenes",        icon: Film },
  { href: "/editor",    label: "Video Editor",  icon: Video },
  { href: "/export",    label: "Render / Export", icon: Download },
];

const bottomItems = [
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={cn(
        "flex flex-col h-full border-r border-white/[0.06] bg-[#0d0d1e] transition-all duration-300",
        collapsed ? "w-[70px]" : "w-64"
      )}
    >
      {/* ── Logo ── */}
      <div className="p-5 flex items-center gap-3 border-b border-white/[0.06]">
        <motion.div
          whileHover={{ scale: 1.08, rotate: 5 }}
          className="size-9 rounded-xl bg-primary flex items-center justify-center text-white shadow-lg shadow-primary/40 flex-shrink-0"
        >
          <Sparkles size={18} />
        </motion.div>
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
            >
              <h1 className="text-sm font-bold text-white leading-none">AI Studio</h1>
              <p className="text-[10px] text-slate-500 uppercase tracking-widest font-semibold mt-0.5">
                Video Engine
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── Navigation ── */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {navItems.map((item, i) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <motion.div
              key={item.href}
              initial={{ opacity: 0, x: -15 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05, duration: 0.3 }}
            >
              <Link href={item.href}>
                <motion.div
                  whileHover={{ x: 3 }}
                  whileTap={{ scale: 0.97 }}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 relative group",
                    collapsed && "justify-center px-2",
                    active
                      ? "bg-primary/15 text-primary border border-primary/20"
                      : "text-slate-400 hover:text-slate-200 hover:bg-white/[0.04]"
                  )}
                >
                  {active && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 bg-primary/10 rounded-xl border border-primary/20"
                      transition={{ type: "spring", duration: 0.4 }}
                    />
                  )}
                  <item.icon
                    size={18}
                    className={cn(
                      "flex-shrink-0 relative z-10",
                      active ? "text-primary" : "text-slate-500 group-hover:text-slate-300"
                    )}
                  />
                  <AnimatePresence>
                    {!collapsed && (
                      <motion.span
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="relative z-10"
                      >
                        {item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                  {/* Tooltip for collapsed state */}
                  {collapsed && (
                    <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded-lg opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                      {item.label}
                    </div>
                  )}
                </motion.div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* ── User & Create ── */}
      <div className="p-3 border-t border-white/[0.06] space-y-2">
        {/* Plan Badge */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="px-3 py-2 rounded-xl bg-gradient-to-r from-primary/10 to-purple-500/10 border border-primary/15"
            >
              <div className="flex items-center gap-2">
                <Zap size={12} className="text-primary" />
                <span className="text-[11px] font-semibold text-primary">Pro Plan Active</span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.97 }}
          onClick={() => setCollapsed(!collapsed)}
          className="w-full flex items-center justify-center gap-2 bg-primary hover:bg-primary-600 text-white py-2.5 rounded-xl text-xs font-bold shadow-lg shadow-primary/25 transition-all"
        >
          <Plus size={14} />
          {!collapsed && <span>New Project</span>}
        </motion.button>

        {/* User Info */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-white/[0.04] cursor-pointer transition-colors group"
            >
              <div className="size-7 rounded-full bg-gradient-to-br from-primary to-purple-500 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                A
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-semibold text-slate-200 truncate">Alex Rivera</p>
                <p className="text-[10px] text-slate-500 truncate">alex@studio.ai</p>
              </div>
              <ChevronUp size={12} className="text-slate-600 group-hover:text-slate-400 transition-colors" />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}
