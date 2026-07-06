"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";
import AdminAuth from "@/components/admin-auth";

interface Product {
  id: string;
  title: string;
  artist: string;
  cover_url: string | null;
  platforms: { platform: string }[];
}

export default function AdminPage() {
  const [token, setToken] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    if (stored) setToken(stored);
    else setLoading(false);
  }, []);

  useEffect(() => {
    if (!token) return;
    loadProducts();
  }, [token]);

  async function loadProducts() {
    setLoading(true);
    const { data } = await supabase
      .from("products")
      .select(`id, title, artist, cover_url, product_platform_config ( platform )`)
      .order("title");
    setProducts((data ?? []) as any);
    setLoading(false);
  }

  async function handleDelete(id: string) {
    if (!token) return;
    if (!confirm("Tem certeza que deseja remover este CD? O histórico de preços também será removido.")) return;

    setDeleting(id);
    try {
      const res = await fetch(`/api/albums/${id}`, {
        method: "DELETE",
        headers: { "x-admin-token": token },
      });
      if (!res.ok) throw new Error("Falha ao deletar");
      setProducts((prev) => prev.filter((p) => p.id !== id));
    } catch (err) {
      alert("Erro ao remover CD.");
    } finally {
      setDeleting(null);
    }
  }

  if (!token) {
    if (loading) return null;
    return <AdminAuth onAuth={(t) => { setToken(t); }} />;
  }

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 24, margin: 0 }}>Gerenciar CDs</h1>
        <p style={{ color: "#6b7280", fontSize: 14, margin: "4px 0 0" }}>
          {products.length} CD{products.length !== 1 ? "s" : ""} na lista
        </p>
      </div>

      <div style={{ marginBottom: 20, display: "flex", gap: 12 }}>
        <a
          href="/gerenciar/adicionar"
          style={{
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            background: "#111827",
            border: "none",
            borderRadius: 6,
            textDecoration: "none",
          }}
        >
          + Adicionar CD
        </a>
        <a
          href="/gerenciar/logs"
          style={{
            padding: "10px 20px",
            fontSize: 14,
            fontWeight: 600,
            color: "#111827",
            background: "#f3f4f6",
            border: "1px solid #d1d5db",
            borderRadius: 6,
            textDecoration: "none",
          }}
        >
          Logs de Scraping
        </a>
      </div>

      {loading ? (
        <p style={{ color: "#9ca3af" }}>Carregando...</p>
      ) : products.length === 0 ? (
        <p style={{ color: "#9ca3af" }}>Nenhum CD cadastrado ainda.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {products.map((product) => (
            <div
              key={product.id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: "12px 16px",
                background: "#fff",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
              }}
            >
              <div
                style={{
                  width: 40,
                  height: 40,
                  borderRadius: 4,
                  background: "#e5e7eb",
                  flexShrink: 0,
                  overflow: "hidden",
                }}
              >
                {product.cover_url ? (
                  <img src={product.cover_url} alt="" style={{ width: 40, height: 40, objectFit: "cover" }} />
                ) : (
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", fontSize: 18 }}>💿</div>
                )}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{product.title}</div>
                <div style={{ color: "#6b7280", fontSize: 13 }}>{product.artist}</div>
              </div>
              <div style={{ display: "flex", gap: 4 }}>
                {(product.platforms ?? []).map((p) => (
                  <span
                    key={p.platform}
                    style={{
                      fontSize: 11,
                      background: "#f3f4f6",
                      padding: "2px 6px",
                      borderRadius: 4,
                      color: "#6b7280",
                    }}
                  >
                    {p.platform === "amazon" ? "AMZ" : p.platform === "mercado_livre" ? "ML" : "SP"}
                  </span>
                ))}
              </div>
              <button
                type="button"
                onClick={() => handleDelete(product.id)}
                disabled={deleting === product.id}
                style={{
                  padding: "6px 12px",
                  fontSize: 13,
                  color: deleting === product.id ? "#9ca3af" : "#ef4444",
                  background: "#fef2f2",
                  border: "1px solid #fecaca",
                  borderRadius: 6,
                  cursor: deleting === product.id ? "not-allowed" : "pointer",
                  whiteSpace: "nowrap",
                }}
              >
                {deleting === product.id ? "Removendo..." : "Remover"}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
