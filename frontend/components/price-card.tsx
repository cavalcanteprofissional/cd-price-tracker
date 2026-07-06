"use client";

import { useRouter } from "next/navigation";

interface PriceItem {
  platform: string;
  price: number;
  seller_name: string | null;
  listing_url: string;
}

interface PriceCardProps {
  id: string;
  title: string;
  artist: string;
  coverUrl: string | null;
  prices: PriceItem[];
}

const platformLabels: Record<string, string> = {
  amazon: "Amazon BR",
  amazon_us: "Amazon US",
  amazon_uk: "Amazon UK",
  amazon_de: "Amazon DE",
  mercado_livre: "Mercado Livre",
  magalu: "Magazine Luiza",
  americanas: "Americanas",
  casas_bahia: "Casas Bahia",
  submarino: "Submarino",
  carrefour: "Carrefour",
  extra: "Extra",
  shopee: "Shopee",
};

export default function PriceCard({ id, title, artist, coverUrl, prices }: PriceCardProps) {
  const router = useRouter();

  return (
    <div
      onClick={() => router.push(`/produto/${id}`)}
      style={{
        background: "#fff",
        borderRadius: 8,
        padding: 16,
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        cursor: "pointer",
        border: "1px solid #e5e7eb",
        transition: "box-shadow 0.2s",
      }}
      onMouseOver={(e) => (e.currentTarget.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)")}
      onMouseOut={(e) => (e.currentTarget.style.boxShadow = "0 1px 3px rgba(0,0,0,0.1)")}
    >
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        <div
          style={{
            width: 56,
            height: 56,
            borderRadius: 4,
            background: "#e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 24,
            flexShrink: 0,
          }}
        >
          {coverUrl ? (
            <img src={coverUrl} alt="" style={{ width: 56, height: 56, borderRadius: 4, objectFit: "cover" }} />
          ) : (
            "💿"
          )}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {title}
          </h3>
          <p style={{ margin: "2px 0 0", fontSize: 14, color: "#6b7280" }}>{artist}</p>
        </div>
      </div>

      {prices.length > 0 && (
        <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
          {prices.map((p, i) => (
            <a
              key={i}
              href={p.listing_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              style={{
                fontSize: 13,
                background: "#f3f4f6",
                padding: "4px 8px",
                borderRadius: 4,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
                textDecoration: "none",
                color: "inherit",
              }}
            >
              {platformLabels[p.platform] ?? p.platform}: <strong>R$ {Number(p.price).toFixed(2)}</strong>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
