import { NextResponse } from "next/server";

const LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const q = searchParams.get("q");

  if (!q || q.trim().length < 2) {
    return NextResponse.json({ results: [] });
  }

  const apiKey = process.env.LASTFM_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ error: "Last.fm API key not configured" }, { status: 500 });
  }

  const url = `${LASTFM_API_URL}?method=album.search&album=${encodeURIComponent(q)}&api_key=${apiKey}&format=json&limit=10`;

  try {
    const res = await fetch(url, { next: { revalidate: 60 } });
    if (!res.ok) throw new Error(`Last.fm returned ${res.status}`);

    const data = await res.json();
    const albums = data.results?.albummatches?.album ?? [];

    const results = albums.map((a: any) => ({
      title: a.name,
      artist: a.artist,
      url: a.url,
      cover: a.image?.find((i: any) => i.size === "mega" || i.size === "extralarge")?.["#text"]
        || a.image?.find((i: any) => i.size === "large")?.["#text"]
        || null,
      listeners: a.listeners ? Number(a.listeners) : null,
      mbid: a.mbid || null,
    }));

    return NextResponse.json({ results });
  } catch (err) {
    console.error("Last.fm search error:", err);
    return NextResponse.json({ error: "Failed to search albums" }, { status: 502 });
  }
}
