import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export async function POST(request: Request) {
  const adminToken = request.headers.get("x-admin-token");
  if (adminToken !== process.env.ADMIN_TOKEN) {
    console.warn("POST /api/albums/add — unauthorized attempt");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const { title, artist, cover_url, lastfm_url, release_date, genre, platforms } = body;

    if (!title || typeof title !== "string" || !artist || typeof artist !== "string" || !platforms || !Array.isArray(platforms) || platforms.length === 0) {
    console.warn("POST /api/albums/add — invalid body: %j", { title, artist, platforms });
    return NextResponse.json({ error: "title, artist, and at least one platform required" }, { status: 400 });
  }

  console.log("POST /api/albums/add — title=%s, artist=%s, platforms=%j", title, artist, platforms);

  const { data: product, error: productError } = await supabase
    .from("products")
    .insert({
      title,
      artist,
      cover_url: cover_url || null,
      lastfm_url: lastfm_url || null,
      release_date: release_date || null,
      genre: genre || [],
    })
    .select("id")
    .single();

  if (productError) {
    console.error("POST /api/albums/add — product insert error:", productError);
    return NextResponse.json({ error: "Failed to create product" }, { status: 500 });
  }

  console.log("POST /api/albums/add — created product id=%s", product.id);

  const configs = platforms.map((platform: string) => ({
    product_id: product.id,
    platform,
    amazon_url: null,
    search_query: null,
  }));

  const { error: configError } = await supabase
    .from("product_platform_config")
    .insert(configs);

  if (configError) {
    await supabase.from("products").delete().eq("id", product.id);
    console.error("POST /api/albums/add — config insert error:", configError);
    return NextResponse.json({ error: "Failed to create platform configs" }, { status: 500 });
  }

  console.log("POST /api/albums/add — success, %d configs created", configs.length);
  return NextResponse.json({ id: product.id });
}
