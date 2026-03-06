"use client";

import { motion, AnimatePresence } from "framer-motion";
import { ReactNode } from "react";
import Sidebar from "./Sidebar";

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  return (
    <div className="flex h-screen overflow-hidden bg-background-dark">
      <Sidebar />
      <AnimatePresence mode="wait">
        <motion.main
          key={typeof window !== "undefined" ? window.location.pathname : ""}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.28, ease: "easeInOut" }}
          className="flex-1 flex flex-col overflow-hidden"
        >
          {children}
        </motion.main>
      </AnimatePresence>
    </div>
  );
}
