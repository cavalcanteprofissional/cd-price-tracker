import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CD Price Tracker",
  description: "Acompanhe os preços dos seus CDs favoritos",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-BR">
      <body style={{ margin: 0, fontFamily: "system-ui, sans-serif", background: "#f9fafb", color: "#111827" }}>
        <nav style={{ background: "#111827", color: "#fff", padding: "16px 24px" }}>
          <a href="/" style={{ color: "#fff", textDecoration: "none", fontWeight: 700, fontSize: 18 }}>
            CD Price Tracker
          </a>
        </nav>
        <main style={{ maxWidth: 960, margin: "0 auto", padding: 24 }}>
          {children}
        </main>
      </body>
    </html>
  );
}
