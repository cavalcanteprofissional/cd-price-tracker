import { NextResponse } from "next/server";

export async function GET(request: Request) {
  const adminToken = request.headers.get("x-admin-token");
  if (adminToken !== process.env.ADMIN_TOKEN) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  return NextResponse.json({ ok: true });
}
