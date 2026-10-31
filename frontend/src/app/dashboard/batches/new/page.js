"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { batches } from "@/lib/api";

export default function NewBatchPage() {
  const router = useRouter();
  const [form, setForm] = useState({ department: "", batch_year: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const DEPARTMENTS = [
    "Computer Science and Engineering",
    "Information Technology",
    "Electronics and Communication Engineering",
    "Electrical and Electronics Engineering",
    "Mechanical Engineering",
    "Civil Engineering",
    "Artificial Intelligence and Data Science",
    "Cyber Security",
    "Computer Science and Business Systems",
  ];

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const batch = await batches.create(form.department, form.batch_year);
      router.push(`/dashboard/batches/${batch.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <span className="current">New Batch</span>
          </div>
          <h1>Create a <span className="gradient-text">New Batch</span></h1>
        </div>
      </div>

      <div className="card" style={{ maxWidth: 520, padding: 36 }}>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {error && <div className="alert alert-error">{error}</div>}

          <div className="form-group">
            <label className="form-label">Department</label>
            <select
              className="form-input"
              value={form.department}
              onChange={set("department")}
              required
              style={{ cursor: "pointer" }}
            >
              <option value="" disabled>Select department…</option>
              {DEPARTMENTS.map((d) => (
                <option key={d} value={d} style={{ background: "var(--bg-surface)" }}>{d}</option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Batch Year</label>
            <input
              className="form-input"
              type="text"
              placeholder="e.g. 2023-2027"
              value={form.batch_year}
              onChange={set("batch_year")}
              required
              pattern="\d{4}-\d{4}"
              title="Format: YYYY-YYYY"
            />
            <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
              Format: YYYY-YYYY (e.g. 2023-2027)
            </span>
          </div>

          <div style={{ display: "flex", gap: 12 }}>
            <Link href="/dashboard" className="btn btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
              Cancel
            </Link>
            <button
              className="btn btn-primary"
              type="submit"
              disabled={loading}
              style={{ flex: 2, justifyContent: "center" }}
            >
              {loading ? <span className="spinner" /> : "Create Batch"}
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
