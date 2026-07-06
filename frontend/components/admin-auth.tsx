"use client";

import { useState } from "react";

interface AdminAuthProps {
  onAuth: (token: string) => void;
}

export default function AdminAuth({ onAuth }: AdminAuthProps) {
  const [token, setToken] = useState("");
  const [error, setError] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (token.trim().length < 8) {
      setError(true);
      return;
    }
    sessionStorage.setItem("admin_token", token.trim());
    onAuth(token.trim());
  }

  return (
    <div style={{ maxWidth: 400, margin: "60px auto", textAlign: "center" }}>
      <h2 style={{ fontSize: 20, marginBottom: 8 }}>Acesso Restrito</h2>
      <p style={{ color: "#6b7280", marginBottom: 20, fontSize: 14 }}>
        Digite o token de administrador para gerenciar os CDs.
      </p>
      <form onSubmit={handleSubmit}>
        <input
          type="password"
          value={token}
          onChange={(e) => { setToken(e.target.value); setError(false); }}
          placeholder="Token de administrador"
          style={{
            width: "100%",
            padding: "10px 12px",
            fontSize: 14,
            border: `1px solid ${error ? "#ef4444" : "#d1d5db"}`,
            borderRadius: 6,
            outline: "none",
            boxSizing: "border-box",
          }}
        />
        {error && (
          <p style={{ color: "#ef4444", fontSize: 13, marginTop: 6 }}>Token inválido.</p>
        )}
        <button
          type="submit"
          style={{
            width: "100%",
            marginTop: 12,
            padding: "10px 16px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            background: "#111827",
            border: "none",
            borderRadius: 6,
            cursor: "pointer",
          }}
        >
          Entrar
        </button>
      </form>
    </div>
  );
}
