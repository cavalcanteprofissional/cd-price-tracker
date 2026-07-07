"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import AdminAuth from "@/components/admin-auth";

interface LogEntry {
  id: string;
  status: string;
  raw_title: string | null;
  detail: string | null;
  scraped_at: string;
  product_platform_config: {
    id: string;
    platform: string;
    products: { id: string; title: string; artist: string } | null;
  } | null;
}

interface LogsResponse {
  logs: LogEntry[];
  total: number;
}

const statusLabels: Record<string, string> = {
  success: "Sucesso",
  error: "Erro",
  not_found: "Não encontrado",
  skipped_fanmade: "Fanmade ignorado",
};

const statusColors: Record<string, string> = {
  success: "#16a34a",
  error: "#dc2626",
  not_found: "#f59e0b",
  skipped_fanmade: "#6b7280",
};

const platformLabels: Record<string, string> = {
  amazon: "Amazon BR",
  amazon_us: "Amazon US",
  amazon_uk: "Amazon UK",
  amazon_de: "Amazon DE",
  mercado_livre: "Mercado Livre",
  magalu: "Magazine Luiza",
  americanas: "Americanas",
  casas_bahia: "Casas Bahia",
  submarino: "Submarino",
  carrefour: "Carrefour",
  extra: "Extra",
  shopee: "Shopee",
  enjoei: "Enjoei",
};

export default function LogsPage() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<LogsResponse | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [platformFilter, setPlatformFilter] = useState("");

  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    if (stored) setToken(stored);
    else setLoading(false);
  }, []);

  useEffect(() => {
    if (!token) return;
    loadLogs();
  }, [token, statusFilter, platformFilter]);

  async function loadLogs() {
    setLoading(true);
    const params = new URLSearchParams();
    if (statusFilter) params.set("status", statusFilter);
    if (platformFilter) params.set("platform", platformFilter);
    params.set("limit", "200");

    try {
      const res = await fetch(`/api/scrape-logs?${params}`, {
        headers: { "x-admin-token": token! },
      });
      if (!res.ok) throw new Error("Falha ao carregar logs");
      setData(await res.json());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }

  if (!token) {
    if (loading) return null;
    return <AdminAuth onAuth={(t) => setToken(t)} />;
  }

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, margin: 0 }}>Logs de Scraping</h1>
          <p style={{ color: "#6b7280", fontSize: 14, margin: "4px 0 0" }}>
            {data ? `${data.total} registro${data.total !== 1 ? "s" : ""}` : ""}
          </p>
        </div>
        <Link
          href="/gerenciar"
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
          Voltar
        </Link>
      </div>

      <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            fontSize: 14,
          }}
        >
          <option value="">Todos os status</option>
          {Object.entries(statusLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>

        <select
          value={platformFilter}
          onChange={(e) => setPlatformFilter(e.target.value)}
          style={{
            padding: "8px 12px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            fontSize: 14,
          }}
        >
          <option value="">Todas as plataformas</option>
          {Object.entries(platformLabels).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
      </div>

      {loading ? (
        <p style={{ color: "#9ca3af" }}>Carregando...</p>
      ) : !data || data.logs.length === 0 ? (
        <p style={{ color: "#9ca3af" }}>Nenhum log encontrado.</p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
            <thead>
              <tr style={{ borderBottom: "2px solid #e5e7eb", textAlign: "left" }}>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Data</th>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Produto</th>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Plataforma</th>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Status</th>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Título</th>
                <th style={{ padding: "10px 12px", color: "#6b7280", fontWeight: 600 }}>Detalhe</th>
              </tr>
            </thead>
            <tbody>
              {data.logs.map((log) => {
                const product = log.product_platform_config?.products;
                const platform = log.product_platform_config?.platform;
                return (
                  <tr key={log.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "10px 12px", whiteSpace: "nowrap", color: "#6b7280" }}>
                      {new Date(log.scraped_at).toLocaleString("pt-BR")}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      {product ? `${product.title} — ${product.artist}` : "—"}
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{
                        fontSize: 12,
                        background: "#f3f4f6",
                        padding: "2px 8px",
                        borderRadius: 4,
                      }}>
                        {platform ? (platformLabels[platform] ?? platform) : "—"}
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px" }}>
                      <span style={{
                        fontSize: 12,
                        color: "#fff",
                        background: statusColors[log.status] ?? "#6b7280",
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontWeight: 600,
                      }}>
                        {statusLabels[log.status] ?? log.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px 12px", maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {log.raw_title ?? "—"}
                    </td>
                    <td style={{ padding: "10px 12px", maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "#6b7280" }}>
                      {log.detail ?? "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
