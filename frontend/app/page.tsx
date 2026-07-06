export const dynamic = "force-dynamic";

import { supabase } from "@/lib/supabase";
import PriceCard from "@/components/price-card";

async function getProducts() {
  const { data } = await supabase
    .from("products")
    .select(`
      id, title, artist, cover_url,
      product_platform_config (
        id, platform,
        price_history (price, seller_name, listing_url, scraped_at)
      )
    `)
    .order("title");

  return data ?? [];
}

export default async function Home() {
  const products = await getProducts();

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 8 }}>CDs Monitorados</h1>
      <p style={{ color: "#6b7280", marginBottom: 24 }}>
        Preços mais recentes coletados semanalmente
      </p>

      {products.length === 0 && (
        <p style={{ color: "#9ca3af" }}>Nenhum CD cadastrado ainda.</p>
      )}

      <div style={{ display: "grid", gap: 16, gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))" }}>
        {products.map((product: any) => {
          const configs = product.product_platform_config ?? [];
          const latestPrices = configs
            .map((cfg: any) => {
              const prices = cfg.price_history ?? [];
              if (prices.length === 0) return null;
              const latest = prices.reduce((a: any, b: any) =>
                new Date(a.scraped_at) > new Date(b.scraped_at) ? a : b
              );
              return { platform: cfg.platform, ...latest };
            })
            .filter(Boolean);

          return (
            <PriceCard
              key={product.id}
              id={product.id}
              title={product.title}
              artist={product.artist}
              coverUrl={product.cover_url}
              prices={latestPrices}
            />
          );
        })}
      </div>
    </div>
  );
}
