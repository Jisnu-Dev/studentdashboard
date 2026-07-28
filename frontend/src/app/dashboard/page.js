"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { batches } from "@/lib/api";
import { Plus, BookOpen, LayoutDashboard } from "@/lib/icons";

export default function DashboardPage() {
  const router = useRouter();
  const [batchList, setBatchList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    batches.list()
      .then(setBatchList)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const totalDepts = new Set(batchList.map((b) => b.department)).size;

  return (
    <>
      <div className="page-header">
        <div>
          <div className="breadcrumb"><span className="current">Dashboard</span></div>
          <h1>Your <span className="gradient-text">Batches</span></h1>
        </div>
        <Link href="/dashboard/batches/new" className="btn btn-primary">
          <Plus size={16} strokeWidth={2} />
          New Batch
        </Link>
      </div>

      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{batchList.length}</div>
          <div className="stat-label">Total Batches</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{totalDepts}</div>
          <div className="stat-label">Departments</div>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}

      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "64px" }}>
          <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
        </div>
      )}

      {!loading && batchList.length === 0 && (
        <div className="card empty-state">
          <div className="empty-icon"><BookOpen size={40} strokeWidth={1.2} /></div>
          <h3>No batches yet</h3>
          <p style={{ marginBottom: 24 }}>Create your first batch to start managing students.</p>
          <Link href="/dashboard/batches/new" className="btn btn-primary">
            <Plus size={16} /> Create First Batch
          </Link>
        </div>
      )}

      {!loading && batchList.length > 0 && (
        <div className="batch-grid">
          {batchList.map((batch) => (
            <div
              key={batch.id}
              className="card batch-card"
              onClick={() => router.push(`/dashboard/batches/${batch.id}`)}
            >
              <div className="batch-card-dept">{batch.department}</div>
              <div className="batch-card-year">{batch.batch_year}</div>
              <div className="batch-card-meta">
                <span className="badge badge-purple">Batch #{batch.id}</span>
                <span style={{ marginLeft: "auto", fontSize: "0.75rem" }}>
                  {new Date(batch.created_at).toLocaleDateString("en-IN", {
                    day: "numeric", month: "short", year: "numeric"
                  })}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}
