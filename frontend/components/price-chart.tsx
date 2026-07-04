"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface PriceEntry {
  id: string;
  price: number;
  scraped_at: string;
  seller_name: string | null;
}

interface PriceChartProps {
  prices: PriceEntry[];
}

export default function PriceChart({ prices }: PriceChartProps) {
  if (prices.length === 0) {
    return <p style={{ color: "#9ca3af", fontSize: 14 }}>Nenhum histórico disponível.</p>;
  }

  const sorted = [...prices]
    .sort((a, b) => new Date(a.scraped_at).getTime() - new Date(b.scraped_at).getTime())
    .map((p) => ({
      date: new Date(p.scraped_at).toLocaleDateString("pt-BR"),
      price: Number(p.price),
    }));

  const lastPrice = sorted[sorted.length - 1].price;
  const firstPrice = sorted[0].price;
  const change = lastPrice - firstPrice;
  const changePercent = firstPrice > 0 ? ((change / firstPrice) * 100).toFixed(1) : "—";

  return (
    <div>
      <div style={{ marginBottom: 12, fontSize: 14, color: "#6b7280" }}>
        Variação no período:{" "}
        <span style={{ color: change <= 0 ? "#16a34a" : "#dc2626", fontWeight: 600 }}>
          {change >= 0 ? "+" : ""}R$ {change.toFixed(2)} ({changePercent}%)
        </span>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={sorted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="date" stroke="#9ca3af" fontSize={12} />
          <YAxis
            stroke="#9ca3af"
            fontSize={12}
            tickFormatter={(v) => `R$${v.toFixed(2)}`}
            domain={["auto", "auto"]}
          />
          <Tooltip formatter={(value: number) => [`R$ ${value.toFixed(2)}`, "Preço"]} />
          <Line
            type="monotone"
            dataKey="price"
            stroke="#2563eb"
            strokeWidth={2}
            dot={{ r: 4, fill: "#2563eb" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
