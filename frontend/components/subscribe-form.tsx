"use client";

import { useState, FormEvent } from "react";

export default function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const res = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (res.ok) {
        setStatus("success");
        setMessage("Email cadastrado! Verifique sua caixa de entrada para confirmar.");
      } else {
        setStatus("error");
        setMessage(data.error ?? "Erro ao cadastrar. Tente novamente.");
      }
    } catch {
      setStatus("error");
      setMessage("Erro de conexão. Tente novamente.");
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <label htmlFor="email" style={{ fontSize: 14, fontWeight: 500 }}>
        Email
      </label>

      <div style={{ display: "flex", gap: 8 }}>
        <input
          id="email"
          type="email"
          required
          placeholder="seu@email.com"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{
            flex: 1,
            padding: "10px 12px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            fontSize: 14,
          }}
        />
        <button
          type="submit"
          disabled={status === "loading"}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "none",
            background: status === "loading" ? "#9ca3af" : "#111827",
            color: "#fff",
            fontSize: 14,
            fontWeight: 500,
            cursor: status === "loading" ? "not-allowed" : "pointer",
          }}
        >
          {status === "loading" ? "Enviando..." : "Cadastrar"}
        </button>
      </div>

      {message && (
        <p style={{ fontSize: 14, color: status === "success" ? "#16a34a" : "#dc2626" }}>
          {message}
        </p>
      )}
    </form>
  );
}
