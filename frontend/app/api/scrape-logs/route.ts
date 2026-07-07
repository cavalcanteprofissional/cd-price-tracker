import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export async function GET(request: Request) {
  const adminToken = request.headers.get("x-admin-token");
  const expectedToken = process.env.ADMIN_TOKEN?.trim();
  if (adminToken !== expectedToken) {
    console.error("scrape-logs ADMIN_TOKEN mismatch:", {
      received: adminToken,
      expectedLength: expectedToken?.length,
      receivedLength: adminToken?.length,
    });
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(request.url);
  const statusFilter = searchParams.get("status");
  const productId = searchParams.get("product_id");
  const platform = searchParams.get("platform");
  const since = searchParams.get("since");
  const limit = Math.min(Number(searchParams.get("limit")) || 100, 200);
  const offset = Number(searchParams.get("offset")) || 0;

  let query = supabase
    .from("scrape_log")
    .select(`
      id, status, raw_title, detail, scraped_at,
      product_platform_config (
        id, platform,
        products (id, title, artist)
      )
    `, { count: "exact" })
    .order("scraped_at", { ascending: false })
    .range(offset, offset + limit - 1);

  if (statusFilter) {
    query = query.eq("status", statusFilter);
  }
  if (productId) {
    query = query.eq("product_platform_config.product_id", productId);
  }
  if (platform) {
    query = query.eq("product_platform_config.platform", platform);
  }
  if (since) {
    query = query.gte("scraped_at", since);
  }

  const { data, error, count } = await query;

  if (error) {
    console.error("GET /api/scrape-logs error:", error);
    return NextResponse.json({ error: "Failed to fetch logs" }, { status: 500 });
  }

  return NextResponse.json({ logs: data ?? [], total: count ?? 0 });
}
