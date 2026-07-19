"use client";

import { useState } from "react";

interface AdminAuthProps {
  onAuth: (token: string) => void;
}

export default function AdminAuth({ onAuth }: AdminAuthProps) {
  const [token, setToken] = useState("");
  const [error, setError] = useState(false);
  const [validating, setValidating] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(false);

    if (token.trim().length < 8) {
      setError(true);
      return;
    }

    setValidating(true);
    try {
      const res = await fetch("/api/auth/verify", {
        headers: { "x-admin-token": token.trim() },
      });

      if (!res.ok) {
        setError(true);
        return;
      }

      sessionStorage.setItem("admin_token", token.trim());
      onAuth(token.trim());
    } catch {
      setError(true);
    } finally {
      setValidating(false);
    }
  }

  return (
    <div style={{ maxWidth: 400, margin: "60px auto", textAlign: "center" }}>
      <h2 style={{ fontSize: 20, marginBottom: 8 }}>Acesso Restrito</h2>
      <p style={{ color: "#6b7280", marginBottom: 20, fontSize: 14 }}>
        Digite o token de administrador para gerenciar os CDs.
      </p>
      <form onSubmit={handleSubmit}>
        <div style={{ position: "relative" }}>
          <input
            type={showPassword ? "text" : "password"}
            value={token}
            onChange={(e) => { setToken(e.target.value); setError(false); }}
            placeholder="Token de administrador"
            disabled={validating}
            style={{
              width: "100%",
              padding: "10px 36px 10px 12px",
              fontSize: 14,
              border: `1px solid ${error ? "#ef4444" : "#d1d5db"}`,
              borderRadius: 6,
              outline: "none",
              boxSizing: "border-box",
            }}
          />
          <button
            type="button"
            tabIndex={-1}
            onClick={() => setShowPassword((v) => !v)}
            style={{
              position: "absolute",
              right: 8,
              top: "50%",
              transform: "translateY(-50%)",
              background: "none",
              border: "none",
              cursor: "pointer",
              fontSize: 18,
              lineHeight: 1,
              padding: 0,
              color: "#9ca3af",
            }}
            aria-label={showPassword ? "Ocultar senha" : "Exibir senha"}
          >
            {showPassword ? "👁‍🗨" : "👁"}
          </button>
        </div>
        {error && (
          <p style={{ color: "#ef4444", fontSize: 13, marginTop: 6 }}>Token inválido. Verifique com o administrador.</p>
        )}
        <button
          type="submit"
          disabled={validating}
          style={{
            width: "100%",
            marginTop: 12,
            padding: "10px 16px",
            fontSize: 14,
            fontWeight: 600,
            color: "#fff",
            background: validating ? "#9ca3af" : "#111827",
            border: "none",
            borderRadius: 6,
            cursor: validating ? "not-allowed" : "pointer",
          }}
        >
          {validating ? "Validando..." : "Entrar"}
        </button>
      </form>
    </div>
  );
}
