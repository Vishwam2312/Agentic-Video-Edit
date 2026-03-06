"use client";

import { motion, AnimatePresence, useMotionValue, useTransform, animate } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import {
  Play, Download, ChevronRight, CheckCircle2, Sparkles,
  RefreshCw, X, Info, MonitorPlay, Gauge, Layers, Eye
} from "lucide-react";
import { useState, useEffect, useRef } from "react";

const RENDER_DURATION_MS = 8000;

const renderSpecs = [
  { label: "RESOLUTION",  value: "3840 × 2160 (4K)" },
  { label: "FRAME RATE",  value: "60 FPS"            },
  { label: "CODEC",       value: "H.265 (HEVC)"      },
  { label: "AUDIO",       value: "AAC 320kbps"        },
];

const exportFormats = ["MP4", "MOV", "WebM", "GIF"] as const;

function ProgressRing({ progress }: { progress: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const dash = circ * (progress / 100);

  return (
    <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 120 120">
      <circle cx="60" cy="60" r={r} fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
      <motion.circle
        cx="60" cy="60" r={r}
        fill="none" stroke="#1111d4" strokeWidth="6"
        strokeLinecap="round"
        initial={{ strokeDasharray: `0 ${circ}` }}
        animate={{ strokeDasharray: `${dash} ${circ - dash}` }}
        transition={{ duration: 0.5, ease: "easeOut" }}
      />
    </svg>
  );
}

export default function ExportPage() {
  const [renderProgress, setRenderProgress] = useState(0);
  const [renderState, setRenderState] = useState<"idle" | "rendering" | "done" | "cancelled">("idle");
  const [format, setFormat] = useState<typeof exportFormats[number]>("MP4");
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const startRender = () => {
    setRenderState("rendering");
    setRenderProgress(0);
    const startTime = Date.now();
    intervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min((elapsed / RENDER_DURATION_MS) * 100, 100);
      setRenderProgress(progress);
      if (progress >= 100) {
        clearInterval(intervalRef.current!);
        setRenderState("done");
      }
    }, 100);
  };

  const cancelRender = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setRenderState("cancelled");
    setRenderProgress(0);
  };

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  const eta = renderState === "rendering"
    ? Math.max(0, Math.round(((100 - renderProgress) / 100) * (RENDER_DURATION_MS / 1000)))
    : 0;

  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-slate-500">Projects</span>
          <ChevronRight size={14} className="text-slate-600" />
          <span className="text-slate-300 font-medium">Futuristic Cityscape</span>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={startRender}
            disabled={renderState === "rendering"}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            {renderState === "rendering" ? (
              <motion.div animate={{ rotate: 360 }} transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}>
                <RefreshCw size={14} />
              </motion.div>
            ) : (
              <Play size={14} className="fill-white" />
            )}
            {renderState === "rendering" ? "Rendering…" : "Generate Video"}
          </motion.button>
        </div>
      </header>

      {/* ── Content ── */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-3xl mx-auto space-y-6">

          {/* Title */}
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex items-end justify-between"
          >
            <div>
              <h1 className="text-3xl font-black text-white mb-1">Export Studio</h1>
              <p className="text-slate-500 text-sm">High quality 4K generation using Gen-3 Cinema Engine</p>
            </div>
          </motion.div>

          {/* Video preview card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.45 }}
            className="card overflow-hidden"
          >
            {/* Preview area */}
            <div className="relative aspect-video bg-slate-950 flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-slate-800/60 to-slate-950" />

              {/* Processing overlay */}
              <AnimatePresence>
                {renderState === "rendering" && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="absolute inset-0 bg-slate-950/60 backdrop-blur-sm flex flex-col items-center justify-center gap-4 z-10"
                  >
                    {/* Ring progress */}
                    <div className="relative size-28 flex items-center justify-center">
                      <ProgressRing progress={renderProgress} />
                      <div className="text-center z-10">
                        <p className="text-2xl font-black text-white">{Math.round(renderProgress)}%</p>
                        <p className="text-[10px] text-slate-500 font-medium">complete</p>
                      </div>
                    </div>
                    <p className="text-white font-medium text-sm">Processing frames…</p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Done overlay */}
              <AnimatePresence>
                {renderState === "done" && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="absolute inset-0 flex flex-col items-center justify-center gap-4 z-10"
                  >
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: "spring", stiffness: 300 }}
                      className="size-16 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center"
                    >
                      <CheckCircle2 size={28} className="text-emerald-400" />
                    </motion.div>
                    <p className="text-white font-bold">Render Complete!</p>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Video progress bar (at bottom) */}
              <div className="absolute bottom-0 inset-x-0 p-4 bg-gradient-to-t from-black/70 to-transparent z-20">
                <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden mb-2">
                  <motion.div
                    className="h-full bg-primary rounded-full"
                    style={{ width: "67%" }}
                  />
                </div>
                <div className="flex items-center justify-between text-white/60 text-[11px]">
                  <span>01:42 / 02:30</span>
                  <MonitorPlay className="size-4 opacity-50" />
                </div>
              </div>
            </div>

            {/* ── Render progress section ── */}
            <div className="p-5 border-t border-white/[0.06] bg-white/[0.02] space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AnimatePresence mode="wait">
                    {renderState === "rendering" ? (
                      <motion.div
                        key="spinning"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                      >
                        <RefreshCw size={16} className="text-primary" />
                      </motion.div>
                    ) : renderState === "done" ? (
                      <motion.div key="done" initial={{ scale: 0 }} animate={{ scale: 1 }}>
                        <CheckCircle2 size={16} className="text-emerald-400" />
                      </motion.div>
                    ) : (
                      <motion.div key="idle">
                        <MonitorPlay size={16} className="text-slate-500" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                  <span className="font-semibold text-sm">
                    {renderState === "rendering" ? "Rendering Video" :
                     renderState === "done" ? "Render Complete" :
                     renderState === "cancelled" ? "Render Cancelled" :
                     "Ready to Render"}
                  </span>
                </div>
                <AnimatePresence>
                  {renderState === "rendering" && (
                    <motion.span
                      key="pct"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="text-sm font-black text-primary"
                    >
                      {Math.round(renderProgress)}%
                    </motion.span>
                  )}
                </AnimatePresence>
              </div>

              {/* Progress bar */}
              <div className="h-2.5 w-full bg-white/[0.06] rounded-full overflow-hidden">
                <motion.div
                  className={`h-full rounded-full transition-colors ${
                    renderState === "done" ? "bg-emerald-500" : "bg-primary"
                  }`}
                  animate={{ width: `${renderState === "done" ? 100 : renderProgress}%` }}
                  transition={{ duration: 0.3 }}
                />
              </div>

              <div className="flex items-center justify-between">
                <AnimatePresence>
                  {renderState === "rendering" && (
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="text-sm text-slate-500"
                    >
                      Estimated time remaining:{" "}
                      <span className="text-slate-300 font-medium">{eta}s</span>
                    </motion.p>
                  )}
                  {renderState === "idle" && (
                    <p className="text-sm text-slate-500">Click Generate Video to start rendering</p>
                  )}
                  {renderState === "done" && (
                    <p className="text-sm text-emerald-400 font-medium">Your video is ready for download!</p>
                  )}
                  {renderState === "cancelled" && (
                    <p className="text-sm text-slate-500">Render was cancelled</p>
                  )}
                </AnimatePresence>
                {renderState === "rendering" && (
                  <button
                    onClick={cancelRender}
                    className="text-sm text-red-400 hover:text-red-300 font-medium transition-colors"
                  >
                    Cancel Export
                  </button>
                )}
              </div>
            </div>
          </motion.div>

          {/* ── Download / Success row ── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.45 }}
            className="card p-5 flex items-center justify-between gap-4"
          >
            <div className="flex items-center gap-3">
              <motion.div
                animate={renderState === "done" ? { scale: [1, 1.2, 1] } : {}}
                transition={{ duration: 0.5 }}
                className={`size-10 rounded-xl flex items-center justify-center ${
                  renderState === "done"
                    ? "bg-emerald-500/15 border border-emerald-500/20"
                    : "bg-white/[0.04] border border-white/[0.06]"
                }`}
              >
                <CheckCircle2
                  size={18}
                  className={renderState === "done" ? "text-emerald-400" : "text-slate-600"}
                />
              </motion.div>
              <div>
                <p className="text-sm font-semibold text-white">
                  {renderState === "done" ? "Video ready!" : "Success message placeholder"}
                </p>
                <p className="text-[11px] text-slate-500">
                  {renderState === "done"
                    ? "Your 4K video has been rendered successfully."
                    : "Waiting for render completion to enable download."}
                </p>
              </div>
            </div>
            <motion.button
              whileHover={renderState === "done" ? { scale: 1.04 } : {}}
              whileTap={renderState === "done" ? { scale: 0.96 } : {}}
              disabled={renderState !== "done"}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm transition-all ${
                renderState === "done"
                  ? "bg-primary text-white shadow-lg shadow-primary/25 hover:shadow-primary/40"
                  : "bg-white/[0.04] text-slate-600 border border-white/[0.05] cursor-not-allowed"
              }`}
            >
              <Download size={14} />
              Download Video
            </motion.button>
          </motion.div>

          {/* ── Export format picker ── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.28, duration: 0.45 }}
            className="card p-5 space-y-4"
          >
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Layers size={15} className="text-primary" />
              Export Format
            </h3>
            <div className="flex gap-2 flex-wrap">
              {exportFormats.map((f) => (
                <motion.button
                  key={f}
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => setFormat(f)}
                  className={`px-4 py-2 rounded-xl text-sm font-bold border transition-all ${
                    format === f
                      ? "bg-primary/15 border-primary/30 text-primary"
                      : "bg-white/[0.03] border-white/[0.07] text-slate-500 hover:text-slate-300 hover:border-white/15"
                  }`}
                >
                  {f}
                </motion.button>
              ))}
            </div>
          </motion.div>

          {/* ── Render specs ── */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.34, duration: 0.45 }}
            className="grid grid-cols-2 sm:grid-cols-4 gap-3"
          >
            {renderSpecs.map(({ label, value }) => (
              <div key={label} className="card p-4 text-center">
                <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest mb-1">{label}</p>
                <p className="text-sm font-bold text-white">{value}</p>
              </div>
            ))}
          </motion.div>
        </div>
      </div>
    </AppLayout>
  );
}
