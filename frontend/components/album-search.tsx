"use client";

import { useState, useEffect, useRef, useMemo } from "react";

interface AlbumResult {
  title: string;
  artist: string;
  cover: string | null;
  url: string;
  listeners: number | null;
  mbid: string | null;
}

interface AlbumSearchProps {
  onSelect: (album: AlbumResult) => void;
}

export default function AlbumSearch({ onSelect }: AlbumSearchProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AlbumResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [hasSearched, setHasSearched] = useState(false);
  const [highlightedIndex, setHighlightedIndex] = useState(-1);
  const [artistFilter, setArtistFilter] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>();
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const uniqueArtists = useMemo(() => {
    const seen = new Set<string>();
    return results.filter((r) => {
      if (seen.has(r.artist)) return false;
      seen.add(r.artist);
      return true;
    }).map((r) => r.artist);
  }, [results]);

  const filtered = useMemo(() => {
    if (!artistFilter) return results;
    return results.filter((r) => r.artist === artistFilter);
  }, [results, artistFilter]);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);

    if (query.trim().length < 2) {
      setResults([]);
      setHasSearched(false);
      setError("");
      setArtistFilter(null);
      return;
    }

    timer.current = setTimeout(async () => {
      setLoading(true);
      setError("");
      setHighlightedIndex(-1);
      try {
        const res = await fetch(`/api/albums/search?q=${encodeURIComponent(query.trim())}`);
        if (!res.ok) throw new Error("Erro na busca");
        const data = await res.json();
        setResults(data.results ?? []);
        setHasSearched(true);
        setArtistFilter(null);
      } catch {
        setResults([]);
        setError("Erro ao buscar. Tente novamente.");
        setHasSearched(true);
      } finally {
        setLoading(false);
      }
    }, 400);

    return () => { if (timer.current) clearTimeout(timer.current); };
  }, [query]);

  function clear() {
    setQuery("");
    setResults([]);
    setHasSearched(false);
    setError("");
    setArtistFilter(null);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  }

  function select(index: number) {
    const album = filtered[index];
    if (!album) return;
    onSelect(album);
    setQuery("");
    setResults([]);
    setHasSearched(false);
    setArtistFilter(null);
    setHighlightedIndex(-1);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlightedIndex((prev) =>
        prev < filtered.length - 1 ? prev + 1 : 0
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlightedIndex((prev) =>
        prev > 0 ? prev - 1 : filtered.length - 1
      );
    } else if (e.key === "Enter" && highlightedIndex >= 0) {
      e.preventDefault();
      select(highlightedIndex);
    } else if (e.key === "Escape") {
      clear();
    }
  }

  useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const items = listRef.current.children;
      if (items[highlightedIndex]) {
        (items[highlightedIndex] as HTMLElement).scrollIntoView({ block: "nearest" });
      }
    }
  }, [highlightedIndex]);

  const showResults = filtered.length > 0;
  const showChips = uniqueArtists.length > 1 && !loading && hasSearched && !error;

  return (
    <div>
      <div style={{ position: "relative" }}>
        <span
          style={{
            position: "absolute",
            left: 14,
            top: "50%",
            transform: "translateY(-50%)",
            fontSize: 16,
            color: "#9ca3af",
            pointerEvents: "none",
          }}
        >
          🔍
        </span>

        <input
          ref={inputRef}
          autoFocus
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Buscar álbum ou artista..."
          aria-label="Buscar álbum ou artista"
          style={{
            width: "100%",
            padding: "12px 40px 12px 42px",
            fontSize: 16,
            border: "1px solid #d1d5db",
            borderRadius: 8,
            outline: "none",
            boxSizing: "border-box",
          }}
        />

        {query.length > 0 && !loading && (
          <button
            type="button"
            onClick={clear}
            aria-label="Limpar busca"
            style={{
              position: "absolute",
              right: 8,
              top: "50%",
              transform: "translateY(-50%)",
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 18,
              color: "#9ca3af",
              padding: "4px 8px",
              lineHeight: 1,
            }}
          >
            ✕
          </button>
        )}
      </div>

      {loading && (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginTop: 12, color: "#6b7280", fontSize: 14 }}>
          <span
            style={{
              display: "inline-block",
              width: 14,
              height: 14,
              border: "2px solid #d1d5db",
              borderTopColor: "#111827",
              borderRadius: "50%",
              animation: "spin 0.6s linear infinite",
            }}
          />
          Buscando...
        </div>
      )}

      {error && (
        <p style={{ color: "#ef4444", fontSize: 14, marginTop: 12 }}>{error}</p>
      )}

      {!loading && hasSearched && results.length === 0 && !error && (
        <p style={{ color: "#9ca3af", fontSize: 14, marginTop: 12 }}>
          Nenhum álbum encontrado para &ldquo;{query}&rdquo;
        </p>
      )}

      {showChips && (
        <div style={{ marginTop: 12 }}>
          <span style={{ fontSize: 13, color: "#6b7280", marginRight: 8 }}>
            {artistFilter ? "Filtrando por:" : "Filtrar por artista:"}
          </span>
          <div style={{ display: "inline-flex", flexWrap: "wrap", gap: 4, marginTop: 4 }}>
            {uniqueArtists.map((artist) => {
              const active = artistFilter === artist;
              return (
                <button
                  key={artist}
                  type="button"
                  onClick={() => setArtistFilter(active ? null : artist)}
                  style={{
                    fontSize: 13,
                    padding: "4px 10px",
                    borderRadius: 16,
                    border: active ? "1px solid #111827" : "1px solid #d1d5db",
                    background: active ? "#111827" : "#f3f4f6",
                    color: active ? "#fff" : "#374151",
                    cursor: "pointer",
                    fontWeight: active ? 600 : 400,
                    transition: "all 0.1s",
                  }}
                >
                  {artist}
                  {active && <span style={{ marginLeft: 4, fontSize: 11 }}>✕</span>}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {showResults && (
        <div style={{ marginTop: 8, fontSize: 13, color: "#6b7280" }}>
          {filtered.length} resultado{filtered.length !== 1 ? "s" : ""}
          {artistFilter && ` de "${query}"`}
        </div>
      )}

      {showResults && (
        <div
          ref={listRef}
          style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 4 }}
          role="listbox"
          aria-label="Resultados da busca"
        >
          {filtered.map((album, index) => (
            <button
              key={`${album.artist}-${album.title}`}
              type="button"
              role="option"
              aria-selected={highlightedIndex === index}
              onClick={() => select(index)}
              onMouseEnter={() => setHighlightedIndex(index)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 12,
                padding: 10,
                background: highlightedIndex === index ? "#f3f4f6" : "#fff",
                border: "1px solid #e5e7eb",
                borderRadius: 8,
                cursor: "pointer",
                textAlign: "left",
                width: "100%",
                fontSize: 14,
                transition: "background 0.1s",
              }}
            >
              <div
                style={{
                  width: 44,
                  height: 44,
                  borderRadius: 4,
                  background: "#e5e7eb",
                  flexShrink: 0,
                  overflow: "hidden",
                }}
              >
                {album.cover ? (
                  <img src={album.cover} alt="" style={{ width: 44, height: 44, objectFit: "cover" }} />
                ) : (
                  <div style={{ width: 44, height: 44, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>💿</div>
                )}
              </div>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{album.title}</div>
                <div style={{ color: "#6b7280", fontSize: 13 }}>{album.artist}</div>
              </div>
            </button>
          ))}
        </div>
      )}

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

export type { AlbumResult };
