"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Play, Pause, Volume2, Maximize2, SkipBack, SkipForward } from "lucide-react";
import { useRef, useState, useCallback } from "react";
import { cn } from "@/lib/utils";

interface VideoPlayerProps {
  src?: string;
  poster?: string;
  title?: string;
  className?: string;
}

function formatTime(s: number) {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

export default function VideoPlayer({ src, poster, title, className }: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [playing, setPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(150); // mock 2:30
  const [hovered, setHovered] = useState(false);
  const [progress, setProgress] = useState(28); // mock 28%

  const togglePlay = () => {
    if (videoRef.current) {
      if (playing) videoRef.current.pause();
      else videoRef.current.play();
    }
    setPlaying(!playing);
  };

  const handleProgressClick = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const pct = (e.clientX - rect.left) / rect.width;
    setProgress(pct * 100);
    setCurrentTime(pct * duration);
  }, [duration]);

  return (
    <div
      className={cn(
        "relative bg-black rounded-2xl overflow-hidden group shadow-2xl",
        className
      )}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Video / Poster */}
      {src ? (
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          className="w-full h-full object-cover"
          onTimeUpdate={() => {
            if (videoRef.current) {
              setCurrentTime(videoRef.current.currentTime);
              setProgress((videoRef.current.currentTime / (videoRef.current.duration || 1)) * 100);
            }
          }}
          onLoadedMetadata={() => {
            if (videoRef.current) setDuration(videoRef.current.duration);
          }}
        />
      ) : (
        <div
          className="w-full h-full bg-cover bg-center min-h-[300px] opacity-75"
          style={{
            backgroundImage: poster
              ? `url(${poster})`
              : "linear-gradient(135deg, #0f0f2e 0%, #1a1a40 50%, #0d0d24 100%)",
          }}
        />
      )}

      {/* Center play button */}
      <AnimatePresence>
        {(!playing || hovered) && (
          <motion.div
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.2 }}
            className="absolute inset-0 flex items-center justify-center"
          >
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.92 }}
              onClick={togglePlay}
              className="size-16 rounded-full bg-white/15 backdrop-blur-xl border border-white/25 flex items-center justify-center text-white shadow-2xl"
            >
              {playing ? (
                <Pause size={24} className="fill-white" />
              ) : (
                <Play size={24} className="fill-white ml-1" />
              )}
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom controls gradient overlay */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: hovered ? 1 : 0 }}
        transition={{ duration: 0.25 }}
        className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-black/85 via-black/40 to-transparent"
      >
        {/* Progress bar */}
        <div
          className="relative h-1 bg-white/20 rounded-full cursor-pointer mb-4 group/bar"
          onClick={handleProgressClick}
        >
          <motion.div
            className="absolute top-0 left-0 h-full bg-primary rounded-full"
            style={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
          {/* Thumb */}
          <motion.div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 size-3.5 bg-white rounded-full shadow-lg opacity-0 group-hover/bar:opacity-100 transition-opacity"
            style={{ left: `${progress}%` }}
          />
        </div>

        {/* Controls row */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button className="text-white/60 hover:text-white transition-colors">
              <SkipBack size={16} />
            </button>
            <button
              onClick={togglePlay}
              className="text-white hover:text-primary transition-colors"
            >
              {playing ? <Pause size={20} /> : <Play size={20} className="fill-white" />}
            </button>
            <button className="text-white/60 hover:text-white transition-colors">
              <SkipForward size={16} />
            </button>
            <div className="flex items-center gap-1.5 text-white/60 hover:text-white transition-colors cursor-pointer">
              <Volume2 size={16} />
            </div>
            <span className="text-white text-xs font-mono">
              {formatTime(currentTime)} / {formatTime(duration)}
            </span>
          </div>
          <button className="text-white/60 hover:text-white transition-colors">
            <Maximize2 size={16} />
          </button>
        </div>
      </motion.div>
    </div>
  );
}
