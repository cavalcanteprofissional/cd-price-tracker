"use client";

import { useEffect, useState } from "react";

const ALL_PLATFORMS = [
  { id: "amazon", label: "Amazon BR", icon: "🇧🇷" },
  { id: "amazon_us", label: "Amazon US", icon: "🇺🇸" },
  { id: "amazon_uk", label: "Amazon UK", icon: "🇬🇧" },
  { id: "amazon_de", label: "Amazon DE", icon: "🇩🇪" },
  { id: "mercado_livre", label: "Mercado Livre", icon: "🟡" },
  { id: "magalu", label: "Magazine Luiza", icon: "🟢" },
  { id: "americanas", label: "Americanas", icon: "🔵" },
  { id: "casas_bahia", label: "Casas Bahia", icon: "🔴" },
  { id: "shopee", label: "Shopee", icon: "🛍️" },
  { id: "enjoei", label: "Enjoei", icon: "💛" },
];

interface PlatformManagerProps {
  productId: string;
  initialPlatforms: string[];
}

export default function PlatformManager({ productId, initialPlatforms }: PlatformManagerProps) {
  const [token, setToken] = useState<string | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set(initialPlatforms));
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    setToken(stored);
    setReady(true);
  }, []);

  useEffect(() => {
    setSelected(new Set(initialPlatforms));
  }, [initialPlatforms]);

  function toggle(platformId: string) {
    if (!token) return;
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(platformId)) next.delete(platformId);
      else next.add(platformId);
      return next;
    });
  }

  async function handleSave() {
    if (!token) return;
    setSaving(true);
    setMessage(null);
    try {
      const res = await fetch(`/api/albums/${productId}/platforms`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "x-admin-token": token,
        },
        body: JSON.stringify({ platforms: Array.from(selected) }),
      });
      if (!res.ok) throw new Error("Falha ao salvar");
      setMessage("Salvo!");
    } catch {
      setMessage("Erro ao salvar");
    } finally {
      setSaving(false);
      setTimeout(() => setMessage(null), 3000);
    }
  }

  if (!ready) return null;
  if (!token) return null;

  return (
    <div style={{ marginTop: 32, padding: 20, background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb" }}>
      <h3 style={{ margin: "0 0 4px", fontSize: 16 }}>Plataformas ativas</h3>
      <p style={{ margin: "0 0 12px", fontSize: 13, color: "#6b7280" }}>
        Marque as lojas onde o sistema deve buscar preços.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {ALL_PLATFORMS.map((pf) => {
          const isActive = selected.has(pf.id);
          return (
            <label
              key={pf.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                padding: "8px 12px",
                background: isActive ? "#e8f5e9" : "#fff",
                border: `1px solid ${isActive ? "#4caf50" : "#e5e7eb"}`,
                borderRadius: 6,
                cursor: "pointer",
                fontSize: 14,
                opacity: isActive ? 1 : 0.6,
              }}
            >
              <input type="checkbox" checked={isActive} onChange={() => toggle(pf.id)} />
              <span>{pf.icon}</span>
              <span style={{ fontWeight: isActive ? 600 : 400 }}>{pf.label}</span>
              {isActive && <span style={{ marginLeft: "auto", fontSize: 11, color: "#4caf50" }}>ativo</span>}
            </label>
          );
        })}
      </div>

      <div style={{ marginTop: 12, display: "flex", alignItems: "center", gap: 12 }}>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving}
          style={{
            padding: "8px 20px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            background: saving ? "#9ca3af" : "#111827",
            border: "none",
            borderRadius: 6,
            cursor: saving ? "not-allowed" : "pointer",
          }}
        >
          {saving ? "Salvando..." : "Salvar"}
        </button>
        {message && (
          <span style={{ fontSize: 13, color: message === "Salvo!" ? "#16a34a" : "#dc2626" }}>{message}</span>
        )}
      </div>
    </div>
  );
}
