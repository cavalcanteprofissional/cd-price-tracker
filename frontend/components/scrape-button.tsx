"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { PLATFORM_ICONS } from "@/lib/platforms";

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
  info: { icon: "ℹ️", color: "#2563eb" },
};

const STATUS_DISPLAY: Record<string, string> = {
  success: "encontrado",
  not_found: "não encontrado",
  error: "erro",
  skipped_fanmade: "fanmade ignorado",
};



const LOG_PREFIX = /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} \[\w+\] [\w.]+: /;

export default function ScrapeButton() {
  const [token, setToken] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [startedAt, setStartedAt] = useState<string | null>(null);
  const [mode, setMode] = useState<string | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [liveStatus, setLiveStatus] = useState<LogEntry | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [idleSeconds, setIdleSeconds] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const knownIds = useRef(new Set<string>());
  const lastUpdateAt = useRef<number>(Date.now());
  const isFirstRender = useRef(true);
  const abortRef = useRef<AbortController | null>(null);

  // Salva estado no sessionStorage (pula 1º ciclo para não sobrescrever restauração)
  useEffect(() => {
    if (isFirstRender.current) return;
    const state = { status, startedAt, mode, errorMessage, panelOpen, lastUpdate: lastUpdateAt.current, knownIds: [...knownIds.current] };
    sessionStorage.setItem("scrape_state", JSON.stringify(state));
  }, [status, startedAt, mode, errorMessage, panelOpen]);

  // Restaura estado do sessionStorage na montagem
  useEffect(() => {
    const stored = sessionStorage.getItem("admin_token");
    setToken(stored);

    try {
      const saved = JSON.parse(sessionStorage.getItem("scrape_state") || "{}");
      if (["running", "done", "error", "idle"].includes(saved.status)) setStatus(saved.status);
      if (saved.startedAt) setStartedAt(saved.startedAt);
      if (saved.mode) setMode(saved.mode);
      if (saved.errorMessage) setErrorMessage(saved.errorMessage);
      if (saved.panelOpen) setPanelOpen(true);
      if (saved.lastUpdate) lastUpdateAt.current = saved.lastUpdate;
      if (saved.knownIds) saved.knownIds.forEach((id: string) => knownIds.current.add(id));
    } catch { /* ignora estado corrompido */ }

    isFirstRender.current = false;
  }, []);

  // Sincroniza token do sessionStorage quando a aba ganha foco ou
  // sessionStorage muda (cobre login/logout sem refresh)
  useEffect(() => {
    function syncToken() {
      setToken(sessionStorage.getItem("admin_token"));
    }
    window.addEventListener("focus", syncToken);
    window.addEventListener("storage", syncToken);
    return () => {
      window.removeEventListener("focus", syncToken);
      window.removeEventListener("storage", syncToken);
    };
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

  // Safety: após refresh durante streaming local, reseta se ficar 30s sem eventos
  useEffect(() => {
    if (status === "running" && mode === "local" && idleSeconds > 30) {
      setStatus("idle");
      setLogs([]);
      setLiveStatus(null);
      setPanelOpen(false);
      setErrorMessage(null);
    }
  }, [status, mode, idleSeconds]);

  // Cleanup do AbortController ao desmontar
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Polling — busca logs estruturados do banco (tanto local streaming quanto GHA)
  useEffect(() => {
    if (status !== "running" || !startedAt || !mode) return;

    const interval = setInterval(async () => {
      try {
        const url = `/api/scrape-logs?since=${startedAt}&limit=20`;
        const headers: Record<string, string> = {};
        if (token) headers["x-admin-token"] = token;

        const res = await fetch(url, { headers });
        if (!res.ok) return;
        const data = await res.json();
        const entries: LogEntry[] = (data.logs ?? []).filter(
          (e: LogEntry) => e.product_platform_config != null,
        );

        const newEntries = entries.filter((e) => !knownIds.current.has(e.id));
        for (const e of newEntries) knownIds.current.add(e.id);

        if (newEntries.length > 0) {
          setLogs((prev) => [...newEntries, ...prev].slice(0, 50));
          lastUpdateAt.current = Date.now();
        }

        if (Date.now() - lastUpdateAt.current > 300000) {
          setStatus("done");
        }
      } catch {
        // ignore polling errors
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status, startedAt, token, mode]);

  async function handleClick() {
    if (status === "running") {
      setPanelOpen(!panelOpen);
      return;
    }

    if (!token) return;
    setStatus("running");
    setMode(null);
    setStartedAt(null);
    setLogs([]);
    setErrorMessage(null);
    setElapsed(0);
    setIdleSeconds(0);
    knownIds.current.clear();
    lastUpdateAt.current = Date.now();
    setPanelOpen(true);

    try {
      const res = await fetch("/api/scrape/trigger", {
        method: "POST",
        headers: { "x-admin-token": token },
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Erro desconhecido");
      }

      const contentType = res.headers.get("content-type") || "";

      if (contentType.includes("text/event-stream")) {
        // Streaming local — lê SSE do Python em tempo real
        const reader = res.body!.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        setLiveStatus(null);
        setLogs([]);

        abortRef.current = new AbortController();
        const signal = abortRef.current.signal;

        while (true) {
          if (signal.aborted) { reader.cancel(); break; }
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const event = JSON.parse(line.slice(6));
              switch (event.type) {
                case "start":
                  setStartedAt(event.started_at);
                  setMode(event.mode);
                  lastUpdateAt.current = Date.now();
                  break;
                case "log":
                  setLiveStatus({
                    id: crypto.randomUUID(),
                    status: "info",
                    raw_title: null,
                    detail: event.text,
                    scraped_at: new Date().toISOString(),
                    product_platform_config: null,
                  });
                  lastUpdateAt.current = Date.now();
                  break;
                case "done":
                  setStatus("done");
                  setLiveStatus(null);
                  break;
                case "error":
                  setStatus("error");
                  setLiveStatus(null);
                  setErrorMessage(event.message);
                  break;
              }
            } catch { /* ignore parse errors */ }
          }
        }
      } else {
        // Modo Vercel/GHA — resposta JSON, usa polling
        const data = await res.json();
        setStartedAt(data.started_at);
        setMode(data.mode);
        lastUpdateAt.current = Date.now();
        knownIds.current.clear();
      }
    } catch (e) {
      setStatus("error");
      setErrorMessage(e instanceof Error ? e.message : "Falha ao conectar com o servidor");
    }
  }

  const successCount = useMemo(() => logs.filter((e) => e.status === "success").length, [logs]);
  const errorCount = useMemo(() => logs.filter((e) => e.status === "error").length, [logs]);
  const notFoundCount = useMemo(() => logs.filter((e) => e.status === "not_found").length, [logs]);

  const btnText = useMemo(() => {
    if (status === "running" && startedAt) return `⏳ ${elapsed}s`;
    if (status === "done") {
      const parts: string[] = [];
      if (successCount > 0) parts.push(`${successCount}`);
      if (errorCount > 0) parts.push(`${errorCount} ⚠️`);
      if (notFoundCount > 0) parts.push(`${notFoundCount} ⚪`);
      return parts.length === 0 ? "✅ concluído" : `✅ ${parts.join(" · ")}`;
    }
    if (status === "error") return "❌ Tentar novamente";
    return "▶ Rodar";
  }, [status, startedAt, elapsed, successCount, errorCount, notFoundCount]);

  const btnBg = useMemo(() => {
    if (status === "running") return "#065f46";
    if (status === "done") return errorCount > 0 ? "#92400e" : "#065f46";
    if (status === "error") return "#991b1b";
    return "#1f2937";
  }, [status, errorCount]);

  const doneBanner = status === "done" && logs.length > 0;
  const bannerBg = doneBanner && errorCount > 0 && successCount === 0 ? "#fffbeb" : "#f0fdf4";
  const bannerBorder = doneBanner && errorCount > 0 && successCount === 0 ? "#fde68a" : "#d1fae5";

  if (!token) return null;

  return (
    <>
      <button
        type="button"
        onClick={handleClick}
        style={{
          background: btnBg,
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
        {btnText}
      </button>

      {panelOpen && (status === "running" || status === "done" || status === "error" || logs.length > 0 || liveStatus) && (
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
          <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 16px", borderBottom: doneBanner ? "none" : "1px solid #e5e7eb", background: "#f9fafb" }}>
            <span style={{ fontSize: 14, fontWeight: 600, flex: 1 }}>
              {status === "running"
                ? `⏳ Coletando logs... (${elapsed}s)`
                : status === "done"
                ? `✅ Scraping concluído`
                : `❌ ${errorMessage || "Falha ao iniciar"}`}
            </span>
            <Link href="/gerenciar/logs" style={{ fontSize: 12, color: "#2563eb", textDecoration: "none" }}>
              Ver todos
            </Link>
            <button
              type="button"
               onClick={() => { setPanelOpen(false); setMode(null); setStartedAt(null); if (status === "done" || status === "error") setStatus("idle"); }}
              style={{ background: "none", border: "none", cursor: "pointer", fontSize: 16, color: "#6b7280", padding: 0 }}
            >
              ✕
            </button>
          </div>

          {doneBanner && (
            <div style={{ padding: "8px 16px", fontSize: 12, color: "#374151", background: bannerBg, borderBottom: `1px solid ${bannerBorder}` }}>
              🎉 {successCount} encontrado{successCount !== 1 ? "s" : ""}
              {errorCount > 0 && ` · ${errorCount} erro${errorCount !== 1 ? "s" : ""}`}
              {notFoundCount > 0 && ` · ${notFoundCount} não encontrado${notFoundCount !== 1 ? "" : "s"}`}
              {" · "}{elapsed}s
            </div>
          )}

          {mode && (
            <div style={{ padding: "6px 16px", fontSize: 11, color: "#9ca3af", borderBottom: "1px solid #f3f4f6" }}>
              Modo: {mode === "local" ? "local (exec direto)" : "GitHub Actions"}
            </div>
          )}

          <div style={{ flex: 1, overflowY: "auto", padding: 8 }}>
            {logs.length === 0 && !liveStatus && status === "running" && (
              <p style={{ fontSize: 13, color: "#9ca3af", textAlign: "center", padding: 16 }}>
                Aguardando logs...
              </p>
            )}
            {liveStatus && status === "running" && (() => {
              const time = new Date(liveStatus.scraped_at).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
              return (
                <div key={liveStatus.id} style={{ display: "flex", gap: 8, padding: "6px 8px", fontSize: 12, alignItems: "flex-start", borderBottom: "1px solid #e5e7eb", background: "#f0f7ff" }}>
                  <span style={{ fontSize: 14 }}>ℹ️</span>
                  <div style={{ flex: 1, minWidth: 0, color: "#374151", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {(liveStatus.detail ?? "").replace(LOG_PREFIX, "")}
                  </div>
                  <span style={{ color: "#9ca3af", fontSize: 11, whiteSpace: "nowrap" }}>{time}</span>
                </div>
              );
            })()}
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
                      {STATUS_DISPLAY[entry.status] ?? entry.status}
                      {entry.status === "success" && entry.raw_title && (!product || entry.raw_title !== product.title) ? ` → ${entry.raw_title}` : ""}
                      {entry.detail && entry.status !== "not_found" ? ` — ${entry.detail}` : ""}
                    </div>
                  </div>
                  <span style={{ color: "#9ca3af", fontSize: 11, whiteSpace: "nowrap" }}>{time}</span>
                </div>
              );
            })}
          </div>

          {(logs.length > 0 || liveStatus) && (
            <div style={{ padding: "8px 16px", borderTop: "1px solid #e5e7eb", fontSize: 12, color: "#6b7280", textAlign: "center" }}>
              {logs.filter((e) => e.status === "success").length} encontrado
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
