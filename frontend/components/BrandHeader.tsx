"use client";

import React from "react";
import { Mic, ShieldCheck, Globe } from "lucide-react";

interface BrandHeaderProps {
  status: "idle" | "connecting" | "connected" | "speaking" | "listening" | "ended" | "error";
}

export const BrandHeader: React.FC<BrandHeaderProps> = ({ status }) => {
  const isOnline = status === "connected" || status === "speaking" || status === "listening";

  return (
    <header className="header">
      <div className="container header-inner">
        <div className="brand-logo">
          <div className="brand-icon">B</div>
          <span>BrainCX</span>
        </div>

        <div className="nav-status">
          <span className={`status-dot ${isOnline ? "active" : ""}`} />
          <span>
            {isOnline ? "Voice Session Active" : "Voice Agent Ready"}
          </span>
        </div>
      </div>
    </header>
  );
};
