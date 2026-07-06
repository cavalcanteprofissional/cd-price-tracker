import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export async function PATCH(
  request: Request,
  { params }: { params: { id: string } },
) {
  const adminToken = request.headers.get("x-admin-token");
  if (adminToken !== process.env.ADMIN_TOKEN) {
    console.warn("PATCH /api/albums/[id]/platforms — unauthorized");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await request.json();
  const { platforms } = body;

  if (!Array.isArray(platforms)) {
    return NextResponse.json({ error: "platforms array required" }, { status: 400 });
  }

  console.log("PATCH /api/albums/%s/platforms — syncing platforms=%j", params.id, platforms);

  const { data: existing } = await supabase
    .from("product_platform_config")
    .select("id, platform")
    .eq("product_id", params.id);

  const existingPlatforms = new Set((existing ?? []).map((c: any) => c.platform));
  const newPlatforms = new Set(platforms);

  const toDelete = (existing ?? []).filter((c: any) => !newPlatforms.has(c.platform));
  const toInsert = platforms.filter((p: string) => !existingPlatforms.has(p));

  if (toDelete.length > 0) {
    const ids = toDelete.map((c: any) => c.id);
    const { error } = await supabase
      .from("product_platform_config")
      .delete()
      .in("id", ids);
    if (error) {
      console.error("PATCH platforms — delete error:", error);
      return NextResponse.json({ error: "Failed to remove platforms" }, { status: 500 });
    }
    console.log("PATCH platforms — removed %d configs", ids.length);
  }

  if (toInsert.length > 0) {
    const inserts = toInsert.map((platform: string) => ({
      product_id: params.id,
      platform,
      amazon_url: null,
      search_query: null,
    }));
    const { error } = await supabase
      .from("product_platform_config")
      .insert(inserts);
    if (error) {
      console.error("PATCH platforms — insert error:", error);
      return NextResponse.json({ error: "Failed to add platforms" }, { status: 500 });
    }
    console.log("PATCH platforms — added %d configs", inserts.length);
  }

  return NextResponse.json({ success: true });
}
