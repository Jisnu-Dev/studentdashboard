"use client";
import { useState, useEffect } from "react";

export default function StudentModal({ mode, initial, onSave, onClose }) {
  const [form, setForm] = useState({
    register_number: initial?.register_number || "",
    name: initial?.name || "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onSave(form);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }

  // Close on Escape
  useEffect(() => {
    const handler = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div className="modal-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="modal-box">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
          <h3>{mode === "add" ? "Add Student" : "Edit Student"}</h3>
          <button
            onClick={onClose}
            style={{ background: "none", border: "none", color: "var(--text-muted)", cursor: "pointer", fontSize: "1.2rem" }}
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Register Number</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. 22CS001"
              value={form.register_number}
              onChange={set("register_number")}
              required
              autoFocus
            />
          </div>

          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. Rahul Sharma"
              value={form.name}
              onChange={set("name")}
              required
            />
          </div>

          <div style={{ display: "flex", gap: 12, marginTop: 4 }}>
            <button type="button" className="btn btn-ghost" style={{ flex: 1, justifyContent: "center" }} onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" style={{ flex: 2, justifyContent: "center" }} disabled={loading}>
              {loading ? <span className="spinner" /> : mode === "add" ? "Add Student" : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
