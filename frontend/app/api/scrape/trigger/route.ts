import { NextResponse } from "next/server";
import { exec, spawn } from "child_process";
import path from "path";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

const encoder = new TextEncoder();

function sse(writer: WritableStreamDefaultWriter, data: object) {
  writer.write(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
}

export async function POST(request: Request) {
  try {
    const adminToken = request.headers.get("x-admin-token");
    const expectedToken = process.env.ADMIN_TOKEN?.trim();
    if (adminToken !== expectedToken) {
      console.warn("ADMIN_TOKEN mismatch");
      return NextResponse.json({ error: "Unauthorized — token inválido" }, { status: 401 });
    }

    const startedAt = new Date().toISOString();

    if (process.env.VERCEL) {
      // Vercel: dispatch GitHub Actions workflow
      const GITHUB_PAT = process.env.GITHUB_PAT;
      const owner = process.env.GITHUB_OWNER || "cavalcanteprofissional";
      const repo = process.env.GITHUB_REPO || "cd-price-tracker";

      if (!GITHUB_PAT) {
        return NextResponse.json({ error: "GITHUB_PAT não configurado no servidor" }, { status: 500 });
      }

      const res = await fetch(
        `https://api.github.com/repos/${owner}/${repo}/actions/workflows/weekly-scrape.yml/dispatches`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${GITHUB_PAT}`,
            "Content-Type": "application/json",
            "User-Agent": "cd-price-tracker",
          },
          body: JSON.stringify({ ref: "main" }),
        },
      );

      if (!res.ok) {
        const text = await res.text();
        console.error("GHA dispatch error:", res.status, text);
        return NextResponse.json({ error: "Falha ao disparar GitHub Actions" }, { status: 500 });
      }

      console.log("Scrape trigger: GHA dispatched");
      return NextResponse.json({ status: "triggered", started_at: startedAt, mode: "github_actions" });
    }

    // Local: streaming SSE do Python
    const projectRoot = path.resolve(process.cwd(), "..");
    console.log("Scrape trigger: local streaming from", projectRoot);

    const stream = new TransformStream();
    const writer = stream.writable.getWriter();
    let writerClosed = false;

    function safeSse(data: object) {
      if (!writerClosed) sse(writer, data);
    }

    // Envia evento de start
    safeSse({ type: "start", started_at: startedAt, mode: "local" });

    // Pre-check: python disponível?
    try {
      await new Promise<void>((resolve, reject) => {
        exec("python --version", { timeout: 5000 }, (err) => {
          if (err) reject(new Error("Python não encontrado. Verifique se python está no PATH."));
          else resolve();
        });
      });
    } catch (e) {
      safeSse({ type: "error", message: e instanceof Error ? e.message : "Python não disponível" });
      writerClosed = true;
      writer.close();
      return new Response(stream.readable, {
        headers: { "Content-Type": "text/event-stream", "Cache-Control": "no-cache" },
      });
    }

    // Spawn Python com stdio pipe para streaming
    const child = spawn("python", ["-m", "scraper.main"], {
      cwd: projectRoot,
      env: {
        ...process.env,
        SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
      },
      stdio: ["pipe", "pipe", "pipe"],
    });

    // Forward stdout (prints do Python)
    child.stdout.on("data", (chunk: Buffer) => {
      for (const line of chunk.toString().split("\n").filter(Boolean)) {
        safeSse({ type: "log", text: line });
      }
    });

    // Forward stderr (logging do Python — logger.info etc)
    child.stderr.on("data", (chunk: Buffer) => {
      for (const line of chunk.toString().split("\n").filter(Boolean)) {
        safeSse({ type: "log", text: line });
      }
    });

    // Processo encerrou
    child.on("close", async (code: number | null) => {
      if (code === 0) {
        safeSse({ type: "done", code });
      } else {
        safeSse({ type: "error", message: `Scraper encerrou com código ${code}` });
      }
      writerClosed = true;
      writer.close();
    });

    // Erro ao spawnar (ex: python não encontrado)
    child.on("error", (err: Error) => {
      safeSse({ type: "error", message: `Falha ao iniciar: ${err.message}` });
      writerClosed = true;
      writer.close();
    });

    // Cliente desconectou — mata o processo filho
    request.signal.addEventListener("abort", () => {
      writerClosed = true;
      child.kill();
      writer.close();
    });

    return new Response(stream.readable, {
      headers: {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        Connection: "keep-alive",
      },
    });
  } catch (e) {
    console.error("Scrape trigger: erro inesperado na rota:", e);
    return NextResponse.json({ error: "Erro interno do servidor" }, { status: 500 });
  }
}
