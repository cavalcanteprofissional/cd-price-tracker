"use client";

interface ConfirmModalProps {
  open: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  loading?: boolean;
  danger?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  open,
  title,
  message,
  confirmLabel = "Confirmar",
  cancelLabel = "Cancelar",
  loading = false,
  danger = true,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  if (!open) return null;

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.5)",
        zIndex: 1000,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
      onClick={onCancel}
    >
      <div
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 24,
          maxWidth: 400,
          width: "90%",
          position: "relative",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ fontSize: 18, margin: 0 }}>{title}</h2>
        <p style={{ color: "#6b7280", fontSize: 14, margin: "12px 0 24px", lineHeight: 1.5 }}>
          {message}
        </p>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            style={{
              padding: "8px 16px",
              fontSize: 14,
              color: "#374151",
              background: "#f3f4f6",
              border: "1px solid #d1d5db",
              borderRadius: 6,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            onClick={onConfirm}
            disabled={loading}
            style={{
              padding: "8px 16px",
              fontSize: 14,
              fontWeight: 600,
              color: "#fff",
              background: danger ? (loading ? "#fca5a5" : "#ef4444") : (loading ? "#9ca3af" : "#111827"),
              border: "none",
              borderRadius: 6,
              cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? `${confirmLabel}...` : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
