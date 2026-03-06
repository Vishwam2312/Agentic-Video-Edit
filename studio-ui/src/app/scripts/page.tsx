"use client";

import { motion, AnimatePresence } from "framer-motion";
import AppLayout from "@/components/AppLayout";
import {
  RefreshCw, Save, Bold, Italic, Underline, List,
  Quote, Link2, ChevronRight, Sparkles, Gauge, Plus, X
} from "lucide-react";
import { useState } from "react";

const sampleContent = `<h1>The Neon Horizon</h1>

<p><em>[SCENE 1: OVERHEAD SHOT - TOKYO 2077 - NIGHT]</em></p>
<p>Rain streaks across a cracked windshield. The city lights of Neo-Tokyo blur into a kaleidoscope of cyan and magenta. Our protagonist, <strong>Kaelen</strong>, leans against the hood of a hover-sedan, the smoke from their neural-link glowing faintly in the dark.</p>

<p><em>[NARRATOR (Voice Over)]</em></p>
<blockquote>"They say memory is the first thing to go when you upgrade your wetware. But I remember every glitch. Every neon shadow that didn't move when it was supposed to. In a world of synthetic perfection, I'm looking for the one thing money can't buy: a real heartbeat."</blockquote>

<p><em>[SCENE 2: CLOSE UP - THE DATA CHIP]</em></p>
<p>Kaelen flips a small, crystalline data chip between their fingers. It pulses with a rhythmic amber light. This is the "Ghost-Protocol" — a myth among the street-hackers, and the reason half the Megacorp security teams are currently converging on Sector 4.</p>

<p><em>[MUSIC: LOW SYNTH BASS SWELLS]</em></p>
<p>Footsteps echo in the alley behind. Heavy. Metallic. The sound of a heavy-duty bipedal drone. Kaelen doesn't turn around. They just slot the chip into their wrist-port and smile.</p>`;

const aiSuggestions = [
  {
    type: "Writer Dialogue",
    icon: "✦",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/15",
    content: '"Make the narrator\'s tone more noir-inspired and cynical."',
  },
  {
    type: "Pacing Check",
    icon: "→",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/15",
    content: "Scene 2 feels a bit rushed. Consider adding a brief technical description of the chip hack.",
  },
];

const metadata = [
  { label: "Tone",      value: "Cinematic Noir" },
  { label: "Duration",  value: "~1:45 min"       },
  { label: "Voiceover", value: "Marcus (Deep)"   },
];

export default function ScriptEditorPage() {
  const [saving, setSaving] = useState(false);
  const [regenerating, setRegenerating] = useState(false);
  const [wordCount] = useState(428);

  const handleSave = () => {
    setSaving(true);
    setTimeout(() => setSaving(false), 1500);
  };

  const handleRegenerate = () => {
    setRegenerating(true);
    setTimeout(() => setRegenerating(false), 2000);
  };

  return (
    <AppLayout>
      {/* ── Header ── */}
      <header className="h-16 flex items-center justify-between px-6 border-b border-white/[0.06] bg-background-dark/60 backdrop-blur-md flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <span>Projects</span>
            <ChevronRight size={14} />
            <span className="text-slate-300 font-medium">Cyberpunk Journey 2077</span>
          </div>
          <span className="badge bg-primary/15 text-primary border border-primary/20 text-[10px]">
            DRAFT
          </span>
        </div>
        <div className="flex items-center gap-2">
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleRegenerate}
            disabled={regenerating}
            className="btn-ghost flex items-center gap-2 text-sm py-2"
          >
            <motion.div animate={{ rotate: regenerating ? 360 : 0 }} transition={regenerating ? { duration: 0.8, repeat: Infinity, ease: "linear" } : {}}>
              <RefreshCw size={14} />
            </motion.div>
            Regenerate
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={handleSave}
            disabled={saving}
            className="btn-primary flex items-center gap-2 text-sm py-2"
          >
            <Save size={14} />
            {saving ? "Saving..." : "Save Script"}
          </motion.button>
        </div>
      </header>

      {/* ── Editor workspace ── */}
      <div className="flex-1 flex overflow-hidden">

        {/* ── Text editor pane ── */}
        <div className="flex-1 flex flex-col p-6 overflow-hidden">
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="flex-1 flex flex-col max-w-4xl w-full mx-auto card overflow-hidden"
          >
            {/* Formatting toolbar */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/[0.06] bg-white/[0.02]">
              <div className="flex items-center gap-0.5">
                {[
                  { icon: Bold,      title: "Bold"   },
                  { icon: Italic,    title: "Italic" },
                  { icon: Underline, title: "Underline" },
                ].map(({ icon: Icon, title }) => (
                  <button
                    key={title}
                    title={title}
                    className="size-8 rounded-lg hover:bg-white/[0.06] flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                  >
                    <Icon size={15} />
                  </button>
                ))}
                <div className="w-px h-5 bg-white/10 mx-1.5" />
                {[
                  { icon: List,   title: "List"  },
                  { icon: Quote,  title: "Quote" },
                  { icon: Link2,  title: "Link"  },
                ].map(({ icon: Icon, title }) => (
                  <button
                    key={title}
                    title={title}
                    className="size-8 rounded-lg hover:bg-white/[0.06] flex items-center justify-center text-slate-400 hover:text-white transition-colors"
                  >
                    <Icon size={15} />
                  </button>
                ))}
              </div>
              <span className="text-[11px] text-slate-600 font-medium">
                Words: {wordCount} · Last saved: 2m ago
              </span>
            </div>

            {/* ── Editable content area ── */}
            <div
              className="flex-1 overflow-y-auto p-10 editor-prose bg-transparent focus:outline-none"
              contentEditable
              suppressContentEditableWarning
              dangerouslySetInnerHTML={{ __html: sampleContent }}
            />
          </motion.div>
        </div>

        {/* ── AI suggestions panel ── */}
        <motion.aside
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.15 }}
          className="w-72 flex flex-col border-l border-white/[0.06] bg-background-dark overflow-y-auto"
        >
          <div className="p-5 space-y-5">

            {/* AI Suggestions */}
            <div>
              <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">
                AI Suggestions
              </h3>
              <div className="space-y-3">
                {aiSuggestions.map((s, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + i * 0.1 }}
                    className={`p-3.5 rounded-xl border ${s.border} ${s.bg} group cursor-pointer`}
                  >
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className={`text-sm ${s.color}`}>{s.icon}</span>
                      <span className={`text-xs font-bold ${s.color}`}>{s.type}</span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{s.content}</p>
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      className="mt-2 text-[10px] text-primary font-semibold hover:text-primary-300 transition-colors"
                    >
                      Apply suggestion →
                    </motion.button>
                  </motion.div>
                ))}
              </div>
            </div>

            <div className="h-px bg-white/[0.06]" />

            {/* Script Metadata */}
            <div>
              <h3 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-3">
                Script Metadata
              </h3>
              <div className="space-y-3">
                {metadata.map((m) => (
                  <div key={m.label} className="flex items-center justify-between">
                    <span className="text-xs text-slate-500">{m.label}:</span>
                    <span className="text-xs font-semibold text-primary">{m.value}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="h-px bg-white/[0.06]" />

            {/* Add Scene Reference */}
            <button className="w-full flex items-center justify-center gap-2 py-2.5 rounded-xl border border-dashed border-white/[0.08] text-slate-500 hover:text-slate-300 hover:border-primary/30 text-xs font-medium transition-all group">
              <Plus size={13} className="group-hover:text-primary transition-colors" />
              Add Scene Reference
            </button>

            <div className="h-px bg-white/[0.06]" />

            {/* Ready to Generate */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.6 }}
              className="p-4 rounded-xl bg-gradient-to-b from-primary/15 to-primary/5 border border-primary/20"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <Sparkles size={14} className="text-primary" />
                </motion.div>
                <span className="text-sm font-bold text-white">Ready to Generate?</span>
              </div>
              <p className="text-[11px] text-slate-500 mb-3 leading-relaxed">
                Your script looks solid. Click below to begin rendering your AI video scenes.
              </p>
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
                className="w-full btn-primary text-xs py-2.5"
              >
                Start Video Generation
              </motion.button>
            </motion.div>
          </div>
        </motion.aside>
      </div>
    </AppLayout>
  );
}
