import { NextResponse } from "next/server";
import { createClient } from "@supabase/supabase-js";

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY!,
);

export async function DELETE(
  _request: Request,
  { params }: { params: { id: string } },
) {
  const adminToken = _request.headers.get("x-admin-token");
  if (adminToken !== process.env.ADMIN_TOKEN) {
    console.warn("DELETE /api/albums/[id] — unauthorized attempt");
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  console.log("DELETE /api/albums/[id] — deleting product id=%s", params.id);

  const { error } = await supabase
    .from("products")
    .delete()
    .eq("id", params.id);

  if (error) {
    console.error("DELETE /api/albums/[id] — Supabase error:", error);
    return NextResponse.json({ error: "Failed to delete product" }, { status: 500 });
  }

  console.log("DELETE /api/albums/[id] — success id=%s", params.id);
  return NextResponse.json({ success: true });
}
