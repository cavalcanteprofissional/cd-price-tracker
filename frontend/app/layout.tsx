import type { Metadata } from "next";
import Link from "next/link";
import ScrapeButton from "@/components/scrape-button";

export const metadata: Metadata = {
  title: "CD Price Tracker",
  description: "Acompanhe os preços dos seus CDs favoritos",
  icons: {
    icon: "data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>💿</text></svg>",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f9fafb", color: "#111827" }}>
        <nav style={{ background: "#111827", color: "#fff", padding: "16px 24px", display: "flex", alignItems: "center", gap: 24 }}>
          <Link href="/" style={{ color: "#fff", textDecoration: "none", fontWeight: 700, fontSize: 18 }}>
            CD Price Tracker
          </Link>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginLeft: "auto" }}>
            <ScrapeButton />
            <Link href="/gerenciar" style={{ color: "#9ca3af", textDecoration: "none", fontSize: 14 }}>
              Gerenciar
            </Link>
          </div>
        </nav>
        <main style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>
          {children}
        </main>
      </body>
    </html>
  );
}
