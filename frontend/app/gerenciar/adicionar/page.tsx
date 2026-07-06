"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminAuth from "@/components/admin-auth";
import AlbumSearch from "@/components/album-search";
import PlatformForm from "@/components/platform-form";
import type { AlbumResult } from "@/components/album-search";

export default function AddAlbumPage() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<AlbumResult | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    if (stored) setToken(stored);
    setLoading(false);
  }, []);

  if (loading) return null;

  if (!token) {
    return <AdminAuth onAuth={(t) => setToken(t)} />;
  }

  async function handleSave(platforms: string[]) {
    setSaving(true);
    setError("");
    try {
      const res = await fetch("/api/albums/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-admin-token": token!,
        },
        body: JSON.stringify({
          title: selected!.title,
          artist: selected!.artist,
          cover_url: selected!.cover,
          lastfm_url: selected!.url,
          platforms,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error ?? "Erro ao salvar");
      }

      router.push("/gerenciar");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 4 }}>Adicionar CD</h1>
      <p style={{ color: "#6b7280", fontSize: 14, marginBottom: 24 }}>
        Busque um álbum no Last.fm e escolha as plataformas para monitorar.
      </p>

      {!selected && <AlbumSearch onSelect={(album) => setSelected(album)} />}

      {selected && (
        <PlatformForm
          album={selected}
          onSave={handleSave}
          onCancel={() => setSelected(null)}
          saving={saving}
        />
      )}

      {error && (
        <p style={{ color: "#ef4444", fontSize: 14, marginTop: 16 }}>{error}</p>
      )}
    </div>
  );
}
