"use client";
import { useEffect } from "react";

export default function ConfirmModal({ title, message, danger, loading, onConfirm, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box" style={{ maxWidth: 400 }}>
        <div style={{ textAlign: "center", marginBottom: 24 }}>
          <h3 style={{ marginBottom: 10 }}>{title}</h3>
          <p style={{ fontSize: "0.875rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
            {message}
          </p>
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <button
            className="btn btn-ghost"
            style={{ flex: 1, justifyContent: "center" }}
            onClick={onClose}
            disabled={loading}
          >
            Cancel
          </button>
          <button
            className={`btn ${danger ? "btn-danger" : "btn-primary"}`}
            style={{ flex: 1, justifyContent: "center" }}
            onClick={onConfirm}
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : danger ? "Delete" : "Confirm"}
          </button>
        </div>
      </div>
    </div>
  );
}
