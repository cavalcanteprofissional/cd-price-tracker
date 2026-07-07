"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase } from "@/lib/supabase";
import AdminAuth from "@/components/admin-auth";
import PlatformManager from "@/components/platform-manager";

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
  const [platformTarget, setPlatformTarget] = useState<string | null>(null);

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

  const platformProduct = platformTarget
    ? products.find((p) => p.id === platformTarget)
    : null;

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
        <Link
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
        </Link>
        <Link
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
        </Link>
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
            <Link
              href={`/produto/${product.id}`}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                textDecoration: "none",
                color: "inherit",
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
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>{product.title}</div>
                <div style={{ color: "#6b7280", fontSize: 13 }}>{product.artist}</div>
              </div>
            </Link>
            <div style={{ flex: 1 }} />
            <div style={{ display: "flex", gap: 4, flexWrap: "wrap" }}>
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
                    {p.platform === "amazon" ? "BR" : p.platform === "amazon_us" ? "US" : p.platform === "amazon_uk" ? "UK" : p.platform === "amazon_de" ? "DE" : p.platform === "mercado_livre" ? "ML" : p.platform === "magalu" ? "MGL" : p.platform === "americanas" ? "AM" : p.platform === "casas_bahia" ? "CB" : p.platform === "shopee" ? "SP" : p.platform.toUpperCase().slice(0, 3)}
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
              <button
                type="button"
                onClick={() => setPlatformTarget(product.id)}
                style={{
                  padding: "6px 12px",
                  fontSize: 13,
                  color: "#111827",
                  background: "#f3f4f6",
                  border: "1px solid #d1d5db",
                  borderRadius: 6,
                  cursor: "pointer",
                  whiteSpace: "nowrap",
                }}
              >
                Plataformas
              </button>
            </div>
          ))}
        </div>
      )}

      {platformTarget && platformProduct && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.5)",
            zIndex: 1000,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
          onClick={() => { setPlatformTarget(null); loadProducts(); }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: 12,
              padding: 24,
              maxWidth: 420,
              width: "90%",
              maxHeight: "90vh",
              overflowY: "auto",
              position: "relative",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => { setPlatformTarget(null); loadProducts(); }}
              style={{
                position: "absolute",
                top: 12,
                right: 12,
                background: "none",
                border: "none",
                fontSize: 20,
                cursor: "pointer",
                color: "#6b7280",
                lineHeight: 1,
              }}
            >
              ✕
            </button>
            <div style={{ marginBottom: 12 }}>
              <h2 style={{ fontSize: 18, margin: 0 }}>{platformProduct.title}</h2>
              <p style={{ color: "#6b7280", fontSize: 13, margin: "2px 0 0" }}>{platformProduct.artist}</p>
            </div>
            <PlatformManager
              productId={platformProduct.id}
              initialPlatforms={(platformProduct.platforms ?? []).map((p) => p.platform)}
            />
          </div>
        </div>
      )}
    </div>
  );
}
