"use client";

import { motion, AnimatePresence } from "framer-motion";
import { useCallback, useState } from "react";
import { Upload, FileText, Video, X, CheckCircle, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface UploadFile {
  id: string;
  name: string;
  size: number;
  type: "pdf" | "txt" | "mp4" | "other";
  progress: number;
  status: "uploading" | "complete" | "error";
}

function getFileType(name: string): UploadFile["type"] {
  const ext = name.split(".").pop()?.toLowerCase();
  if (ext === "pdf") return "pdf";
  if (ext === "txt") return "txt";
  if (ext === "mp4") return "mp4";
  return "other";
}

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

const fileTypeIcon = {
  pdf:   <FileText size={20} className="text-red-400" />,
  txt:   <FileText size={20} className="text-blue-400" />,
  mp4:   <Video size={20} className="text-purple-400" />,
  other: <FileText size={20} className="text-slate-400" />,
};

export default function UploadArea() {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);

  const simulateUpload = (file: File) => {
    const id = Math.random().toString(36).slice(2);
    const newFile: UploadFile = {
      id,
      name: file.name,
      size: file.size,
      type: getFileType(file.name),
      progress: 0,
      status: "uploading",
    };
    setFiles((prev) => [...prev, newFile]);

    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 18 + 5;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, progress: 100, status: "complete" } : f))
        );
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === id ? { ...f, progress } : f))
        );
      }
    }, 200);
  };

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      Array.from(e.dataTransfer.files).forEach(simulateUpload);
    },
    []
  );

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      Array.from(e.target.files).forEach(simulateUpload);
    }
  };

  const removeFile = (id: string) =>
    setFiles((prev) => prev.filter((f) => f.id !== id));

  return (
    <div className="space-y-4">
      {/* ── Drop Zone ── */}
      <motion.div
        animate={{
          borderColor: dragging ? "rgba(17,17,212,0.7)" : "rgba(255,255,255,0.08)",
          backgroundColor: dragging ? "rgba(17,17,212,0.07)" : "rgba(255,255,255,0.02)",
          scale: dragging ? 1.01 : 1,
        }}
        transition={{ duration: 0.2 }}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        className="relative rounded-2xl border-2 border-dashed p-12 flex flex-col items-center gap-4 cursor-pointer text-center"
        onClick={() => document.getElementById("file-input")?.click()}
      >
        <input
          id="file-input"
          type="file"
          multiple
          accept=".pdf,.txt,.mp4"
          className="hidden"
          onChange={handleFileInput}
        />

        {/* Animated icon */}
        <motion.div
          animate={{ y: dragging ? -6 : 0 }}
          transition={{ duration: 0.3 }}
          className={cn(
            "size-16 rounded-2xl flex items-center justify-center transition-all duration-300",
            dragging
              ? "bg-primary/20 glow-sm"
              : "bg-white/[0.04] border border-white/[0.06]"
          )}
        >
          <Upload
            size={28}
            className={cn(
              "transition-colors duration-300",
              dragging ? "text-primary" : "text-slate-500"
            )}
          />
        </motion.div>

        <div>
          <p className="text-slate-200 font-semibold text-base mb-1">
            {dragging ? "Release to upload" : "Drag and drop files here"}
          </p>
          <p className="text-slate-500 text-sm">
            Supports PDF (Research papers), TXT (Scripts), or MP4 (Reference videos)
          </p>
          <p className="text-slate-600 text-xs mt-1">Maximum file size: 500MB</p>
        </div>

        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          type="button"
          className="btn-ghost text-sm px-5 py-2.5 mt-2"
          onClick={(e) => e.stopPropagation()}
        >
          Browse Files
        </motion.button>
      </motion.div>

      {/* ── Active Uploads ── */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest">
                Active Uploads
              </h4>
              <span className="text-xs text-slate-500">
                {files.filter((f) => f.status === "uploading").length} uploading
              </span>
            </div>

            {files.map((file) => (
              <motion.div
                key={file.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: -20, height: 0 }}
                transition={{ duration: 0.25 }}
                className="flex items-center gap-3 p-3.5 rounded-xl bg-surface-dark border border-white/[0.05]"
              >
                <div className="size-9 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center flex-shrink-0">
                  {fileTypeIcon[file.type]}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-sm font-medium text-slate-300 truncate max-w-[200px]">
                      {file.name}
                    </span>
                    <span
                      className={cn(
                        "text-xs font-bold",
                        file.status === "complete" ? "text-emerald-400" : "text-primary"
                      )}
                    >
                      {file.status === "complete" ? "Completed" : `${Math.round(file.progress)}%`}
                    </span>
                  </div>
                  <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                    <motion.div
                      className={cn(
                        "h-full rounded-full",
                        file.status === "complete" ? "bg-emerald-500" : "bg-primary"
                      )}
                      initial={{ width: 0 }}
                      animate={{ width: `${file.progress}%` }}
                      transition={{ duration: 0.3 }}
                    />
                  </div>
                  <span className="text-[10px] text-slate-600 mt-0.5 block">
                    {formatBytes(file.size)}
                  </span>
                </div>

                <div className="flex items-center gap-1 flex-shrink-0">
                  {file.status === "complete" && (
                    <CheckCircle size={16} className="text-emerald-400" />
                  )}
                  {file.status === "error" && (
                    <AlertCircle size={16} className="text-red-400" />
                  )}
                  <button
                    onClick={() => removeFile(file.id)}
                    className="size-7 rounded-lg hover:bg-white/10 flex items-center justify-center text-slate-500 hover:text-red-400 transition-colors"
                  >
                    <X size={13} />
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
