"use client";

import { useState } from "react";
import type { AlbumResult } from "./album-search";

interface PlatformFormProps {
  album: AlbumResult;
  onSave: (platforms: string[]) => void;
  onCancel: () => void;
  saving: boolean;
}

const platforms = [
  { id: "amazon", label: "Amazon BR", icon: "🇧🇷" },
  { id: "amazon_us", label: "Amazon US", icon: "🇺🇸" },
  { id: "amazon_uk", label: "Amazon UK", icon: "🇬🇧" },
  { id: "amazon_de", label: "Amazon DE", icon: "🇩🇪" },
  { id: "mercado_livre", label: "Mercado Livre", icon: "🟡" },
  { id: "magalu", label: "Magazine Luiza", icon: "🟢" },
  { id: "americanas", label: "Americanas", icon: "🔵" },
  { id: "casas_bahia", label: "Casas Bahia", icon: "🔴" },
  { id: "shopee", label: "Shopee", icon: "🛍️" },
];

export default function PlatformForm({ album, onSave, onCancel, saving }: PlatformFormProps) {
  const [selected, setSelected] = useState<Set<string>>(new Set(platforms.map(p => p.id)));

  function toggle(platformId: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(platformId)) next.delete(platformId);
      else next.add(platformId);
      return next;
    });
  }

  return (
    <div style={{ marginTop: 24, padding: 20, background: "#f9fafb", borderRadius: 8, border: "1px solid #e5e7eb" }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 16 }}>
        {album.cover && (
          <img
            src={album.cover}
            alt=""
            style={{ width: 56, height: 56, borderRadius: 6, objectFit: "cover" }}
          />
        )}
        <div>
          <h3 style={{ margin: 0, fontSize: 16 }}>{album.title}</h3>
          <p style={{ margin: "2px 0 0", color: "#6b7280", fontSize: 14 }}>{album.artist}</p>
        </div>
      </div>

      <p style={{ margin: "0 0 8px", fontWeight: 600, fontSize: 14 }}>
        Onde você quer monitorar?
      </p>
      <p style={{ margin: "0 0 12px", color: "#6b7280", fontSize: 13 }}>
        O sistema vai buscar o preço automaticamente em cada loja marcada. Todas estão marcadas por padrão.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {platforms.map((pf) => (
          <label
            key={pf.id}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "10px 12px",
              background: selected.has(pf.id) ? "#f3f4f6" : "#fff",
              border: `1px solid ${selected.has(pf.id) ? "#111827" : "#e5e7eb"}`,
              borderRadius: 6,
              cursor: "pointer",
              fontSize: 14,
            }}
          >
            <input
              type="checkbox"
              checked={selected.has(pf.id)}
              onChange={() => toggle(pf.id)}
            />
            <span>{pf.icon}</span>
            <span style={{ fontWeight: selected.has(pf.id) ? 600 : 400 }}>{pf.label}</span>
          </label>
        ))}
      </div>

      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <button
          type="button"
          onClick={() => onSave(Array.from(selected))}
          disabled={saving || selected.size === 0}
          style={{
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            background: saving || selected.size === 0 ? "#9ca3af" : "#111827",
            border: "none",
            borderRadius: 6,
            cursor: saving || selected.size === 0 ? "not-allowed" : "pointer",
          }}
        >
          {saving ? "Salvando..." : "Adicionar à lista"}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={saving}
          style={{
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 500,
            color: "#374151",
            background: "#fff",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          Cancelar
        </button>
      </div>
    </div>
  );
}
