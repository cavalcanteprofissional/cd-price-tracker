"use client";

import { useEffect, useRef, useState } from "react";

interface LogEntry {
  id: string;
  status: string;
  raw_title: string | null;
  detail: string | null;
  scraped_at: string;
  product_platform_config: {
    platform: string;
    products: { title: string; artist: string } | null;
  } | null;
}

const STATUS_LABELS: Record<string, { icon: string; color: string }> = {
  success: { icon: "🟢", color: "#16a34a" },
  error: { icon: "🔴", color: "#dc2626" },
  not_found: { icon: "⚪", color: "#9ca3af" },
  skipped_fanmade: { icon: "⏭️", color: "#f59e0b" },
};

const PLATFORM_ICONS: Record<string, string> = {
  amazon: "🇧🇷", amazon_us: "🇺🇸", amazon_uk: "🇬🇧", amazon_de: "🇩🇪",
  mercado_livre: "🟡", magalu: "🟢", americanas: "🔵", casas_bahia: "🔴", shopee: "🛍️",
};

export default function ScrapeButton() {
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [startedAt, setStartedAt] = useState<string | null>(null);
  const [mode, setMode] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [panelOpen, setPanelOpen] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [idleSeconds, setIdleSeconds] = useState(0);
  const knownIds = useRef(new Set<string>());
  const lastUpdateAt = useRef<number>(Date.now());

  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    setToken(stored);
  }, []);

  // Elapsed timer for button label
  useEffect(() => {
    if (status !== "running" || !startedAt) return;
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [status, startedAt]);

  // Idle timer — atualiza a cada 1s para mostrar "última atualização há Xs"
  useEffect(() => {
    if (status !== "running") return;
    const interval = setInterval(() => {
      setIdleSeconds(Math.floor((Date.now() - lastUpdateAt.current) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [status]);

  // Polling — busca logs a cada 3s, auto-stop após 5min sem novidades
  useEffect(() => {
    if (status !== "running" || !startedAt) return;

    const interval = setInterval(async () => {
      try {
        const url = `/api/scrape-logs?since=${startedAt}&limit=20`;
        const headers: Record<string, string> = {};
        if (token) headers["x-admin-token"] = token;

        const res = await fetch(url, { headers });
        if (!res.ok) return;
        const data = await res.json();
        const entries: LogEntry[] = data.logs ?? [];

        const newEntries = entries.filter((e) => !knownIds.current.has(e.id));
        for (const e of newEntries) knownIds.current.add(e.id);

        if (newEntries.length > 0) {
          setLogs((prev) => [...newEntries, ...prev].slice(0, 50));
          lastUpdateAt.current = Date.now();
        }

        // Auto-stop após 5 minutos sem nenhum log novo
        if (Date.now() - lastUpdateAt.current > 300000) {
          setStatus("done");
        }
      } catch {
        // ignore polling errors
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status, startedAt, token]);

  async function handleClick() {
    if (status === "running") {
      setPanelOpen(!panelOpen);
      return;
    }

    if (!token) return;
    setStatus("running");
    setLogs([]);
    knownIds.current.clear();
    setPanelOpen(true);

    try {
      const res = await fetch("/api/scrape/trigger", {
        method: "POST",
        headers: { "x-admin-token": token },
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setStartedAt(data.started_at);
      setMode(data.mode);
      lastUpdateAt.current = Date.now();
    } catch {
      setStatus("error");
    }
  }

  if (!token) return null;

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        style={{
          background: status === "running" ? "#065f46" : status === "error" ? "#991b1b" : "#1f2937",
          color: "#fff",
          border: "1px solid #374151",
          borderRadius: 6,
          padding: "6px 12px",
          fontSize: 13,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          gap: 6,
          whiteSpace: "nowrap",
        }}
      >
        {status === "running" && startedAt
          ? `⏳ ${elapsed}s`
          : status === "done"
          ? "✅"
          : status === "error"
          ? "❌"
          : "▶ Rodar"}
      </button>

      {panelOpen && (status === "running" || status === "done" || logs.length > 0) && (
        <div
          style={{
            position: "fixed",
            top: 64,
            right: 24,
            width: 420,
            maxHeight: "calc(100vh - 100px)",
            background: "#fff",
            border: "1px solid #e5e7eb",
            borderRadius: 8,
            boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
            zIndex: 1000,
            display: "flex",
            flexDirection: "column",
            overflow: "hidden",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 16px", borderBottom: "1px solid #e5e7eb", background: "#f9fafb" }}>
            <span style={{ fontSize: 14, fontWeight: 600, flex: 1 }}>
              {status === "running"
                ? `⏳ Coletando logs... (${elapsed}s)`
                : status === "done"
                ? "✅ Scraping concluído"
                : "❌ Falha ao iniciar"}
            </span>
            <a href="/gerenciar/logs" style={{ fontSize: 12, color: "#2563eb", textDecoration: "none" }}>
              Ver todos
            </a>
            <button
              type="button"
               onClick={() => { setPanelOpen(false); if (status === "done" || status === "error") setStatus("idle"); }}
              style={{ background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "#6b7280", padding: 0 }}
            >
              ✕
            </button>
          </div>

          {mode && (
            <div style={{ padding: "6px 16px", fontSize: 11, color: "#9ca3af", borderBottom: "1px solid #f3f4f6" }}>
              Modo: {mode === "local" ? "local (exec direto)" : "GitHub Actions"}
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
            {logs.length === 0 && status === "running" && (
              <p style={{ fontSize: 13, color: "#9ca3af", textAlign: "center", padding: 16 }}>
                Aguardando logs...
              </p>
            )}
            {logs.map((entry) => {
              const st = STATUS_LABELS[entry.status] ?? { icon: "❓", color: "#6b7280" };
              const platform = entry.product_platform_config?.platform ?? "";
              const pfIcon = PLATFORM_ICONS[platform] ?? "🏪";
              const product = entry.product_platform_config?.products;
              const time = new Date(entry.scraped_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
              return (
                <div key={entry.id} style={{ display: "flex", gap: 8, padding: "6px 8px", fontSize: 12, alignItems: "flex-start", borderBottom: "1px solid #f9fafb" }}>
                  <span style={{ fontSize: 14 }}>{st.icon}</span>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 500, color: "#111827", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {pfIcon} {platform.replace("_", " ")}
                      {product && ` — ${product.title}`}
                    </div>
                    <div style={{ color: st.color, fontSize: 11 }}>
                      {entry.status === "success" && entry.raw_title ? entry.raw_title : entry.status}
                      {entry.detail && ` — ${entry.detail}`}
                    </div>
                  </div>
                  <span style={{ color: "#9ca3af", fontSize: 11, whiteSpace: "nowrap" }}>{time}</span>
                </div>
              );
            })}
          </div>

          {logs.length > 0 && (
            <div style={{ padding: "8px 16px", borderTop: "1px solid #e5e7eb", fontSize: 12, color: "#6b7280", textAlign: "center" }}>
              {logs.filter((e) => e.status === "success").length} sucesso
              {" | "}
              {logs.filter((e) => e.status === "error").length} erro
              {" | "}
              {logs.filter((e) => e.status === "not_found").length} não encontrado
              {status === "running" && (
                <span style={{ marginLeft: 12, color: idleSeconds > 120 ? "#ef4444" : "#f59e0b" }}>
                  {idleSeconds > 0 ? `📡 ${idleSeconds}s sem atualização` : "⏳ coletando..."}
                </span>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
}
