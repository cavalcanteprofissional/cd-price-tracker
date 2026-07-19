"use client";

import { useEffect } from "react";

interface ToastProps {
  message: string;
  type: "success" | "error" | "info";
  onClose: () => void;
  duration?: number;
}

const COLORS = {
  success: { bg: "#f0fdf4", border: "#86efac", text: "#166534", icon: "✅" },
  error: { bg: "#fef2f2", border: "#fecaca", text: "#991b1b", icon: "❌" },
  info: { bg: "#eff6ff", border: "#93c5fd", text: "#1e40af", icon: "ℹ️" },
};

export default function Toast({ message, type, onClose, duration = 4000 }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const c = COLORS[type];

  return (
    <div
      style={{
        position: "fixed",
        bottom: 24,
        right: 24,
        zIndex: 1100,
        background: c.bg,
        border: `1px solid ${c.border}`,
        borderRadius: 8,
        padding: "12px 16px",
        display: "flex",
        alignItems: "center",
        gap: 8,
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        maxWidth: 360,
        animation: "toastIn 0.3s ease",
      }}
    >
      <span>{c.icon}</span>
      <span style={{ color: c.text, fontSize: 14, flex: 1 }}>{message}</span>
      <button
        type="button"
        onClick={onClose}
        style={{
          background: "none",
          border: "none",
          cursor: "pointer",
          fontSize: 16,
          color: c.text,
          lineHeight: 1,
          padding: 0,
          opacity: 0.6,
        }}
      >
        ✕
      </button>
      <style>{`
        @keyframes toastIn {
          from { opacity: 0; transform: translateY(12px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
