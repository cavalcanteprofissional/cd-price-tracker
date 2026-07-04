import { supabase } from "@/lib/supabase";
import PriceChart from "@/components/price-chart";

interface Props {
  params: { id: string };
}

async function getProduct(id: string) {
  const { data } = await supabase
    .from("products")
    .select(`
      id, title, artist, cover_url,
      product_platform_config (
        id, platform,
        price_history (id, price, seller_name, listing_url, scraped_at)
      )
    `)
    .eq("id", id)
    .single();

  return data;
}

export default async function ProductPage({ params }: Props) {
  const product = await getProduct(params.id);

  if (!product) {
    return <p style={{ color: "#9ca3af" }}>Produto não encontrado.</p>;
  }

  const configs = product.product_platform_config ?? [];

  return (
    <div>
      <a href="/" style={{ color: "#6b7280", fontSize: 14, textDecoration: "none", display: "inline-block", marginBottom: 16 }}>
        &larr; Voltar
      </a>

      <div style={{ display: "flex", gap: 16, alignItems: "center", marginBottom: 24 }}>
        <div
          style={{
            width: 80,
            height: 80,
            borderRadius: 8,
            background: "#e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 36,
            flexShrink: 0,
          }}
        >
          {product.cover_url ? (
            <img src={product.cover_url} alt="" style={{ width: 80, height: 80, borderRadius: 8, objectFit: "cover" }} />
          ) : (
            "💿"
          )}
        </div>
        <div>
          <h1 style={{ margin: 0, fontSize: 24 }}>{product.title}</h1>
          <p style={{ margin: "4px 0 0", fontSize: 16, color: "#6b7280" }}>{product.artist}</p>
        </div>
      </div>

      {configs.length === 0 && (
        <p style={{ color: "#9ca3af" }}>Nenhuma plataforma configurada para este CD.</p>
      )}

      {configs.map((cfg: any) => (
        <div key={cfg.id} style={{ marginBottom: 32 }}>
          <h2 style={{ fontSize: 18, marginBottom: 12, textTransform: "capitalize" }}>
            {cfg.platform.replace("_", " ")}
          </h2>
          <PriceChart prices={cfg.price_history ?? []} />
        </div>
      ))}
    </div>
  );
}
