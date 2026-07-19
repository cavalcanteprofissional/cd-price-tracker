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

  const { error } = await supabase.rpc("sync_product_platforms", {
    p_product_id: params.id,
    p_platforms: platforms,
  });

  if (error) {
    console.error("PATCH platforms — sync error:", error);
    return NextResponse.json({ error: "Failed to sync platforms" }, { status: 500 });
  }

  console.log("PATCH /api/albums/%s/platforms — synced %d platforms", params.id, platforms.length);
  return NextResponse.json({ success: true });
}
