import { NextResponse } from "next/server";
import { exec } from "child_process";
import path from "path";

export async function POST(request: Request) {
  const adminToken = request.headers.get("x-admin-token");
  if (adminToken !== process.env.ADMIN_TOKEN) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const startedAt = new Date().toISOString();

  if (process.env.VERCEL) {
    // Vercel: dispatch GitHub Actions workflow
    const GITHUB_PAT = process.env.GITHUB_PAT;
    const owner = process.env.GITHUB_OWNER || "cavalcanteprofissional";
    const repo = process.env.GITHUB_REPO || "cd-price-tracker";

    if (!GITHUB_PAT) {
      return NextResponse.json({ error: "GITHUB_PAT not configured" }, { status: 500 });
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
      return NextResponse.json({ error: "Failed to trigger GitHub Actions" }, { status: 500 });
    }

    console.log("Scrape trigger: GHA dispatched");
    return NextResponse.json({ status: "triggered", started_at: startedAt, mode: "github_actions" });
  }

  // Local: exec python scraper from project root (same as manual / GHA)
  const projectRoot = path.resolve(process.cwd(), "..");
  console.log("Scrape trigger: local exec from", projectRoot);

  exec(`python -m scraper.main`, {
    cwd: projectRoot,
    env: {
      ...process.env,
      SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    },
    timeout: 600000,
  }, (error, stdout, stderr) => {
    if (error) {
      console.error("Scrape exec error:", error.message);
      return;
    }
    if (stdout) console.log("Scrape stdout:", stdout.slice(0, 500));
    if (stderr) console.error("Scrape stderr:", stderr.slice(0, 500));
  });

  return NextResponse.json({ status: "running", started_at: startedAt, mode: "local" });
}
