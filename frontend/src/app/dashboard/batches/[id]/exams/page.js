"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { exams, batches } from "@/lib/api";
import { getToken } from "@/lib/auth";
import ConfirmModal from "@/components/ConfirmModal";
import { BarChart2, Plus, Pencil, Trash2, FileDown, BookOpen } from "@/lib/icons";

export default function ExamsListPage() {
  const { id: batchId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [examList, setExamList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, list] = await Promise.all([batches.get(batchId), exams.list(batchId)]);
      setBatch(b);
      setExamList(list);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  async function downloadPdf(exam, type) {
    setPdfLoading(`${exam.id}-${type}`);
    try {
      const token = getToken();
      const urlMap = {
        pt1: exams.pt1PdfUrl(batchId, exam.id),
        pt2: exams.pt2PdfUrl(batchId, exam.id),
        semester: exams.semesterPdfUrl(batchId, exam.id),
      };
      const fileMap = { pt1: "pt1_marks", pt2: "pt2_marks", semester: "semester_grades" };
      const res = await fetch(urlMap[type], { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) { const d = await res.json().catch(() => null); throw new Error(d?.detail || "PDF failed"); }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${fileMap[type]}_${exam.semester}_${batch?.batch_year}.pdf`.replace(/ /g, "_");
      a.click(); URL.revokeObjectURL(a.href);
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(null); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await exams.delete(batchId, id); await load(); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return (
    <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
    </div>
  );

  return (
    <>
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
            <span className="sep">›</span>
            <span className="current">Exams</span>
          </div>
          <h1>Exam <span className="gradient-text">Marks</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
        <Link href={`/dashboard/batches/${batchId}/exams/new`} className="btn btn-primary">
          <Plus size={16} strokeWidth={2} /> Setup Exam
        </Link>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{examList.length}</div>
          <div className="stat-label">Exam Records</div>
        </div>
      </div>

      {examList.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><BarChart2 size={40} strokeWidth={1.2} /></div>
          <h3>No exam records yet</h3>
          <p style={{ marginBottom: 24 }}>Set up subject codes and enter marks for your batch.</p>
          <Link href={`/dashboard/batches/${batchId}/exams/new`} className="btn btn-primary">
            <Plus size={16} /> Setup Exam
          </Link>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {examList.map((exam) => (
            <div key={exam.id} className="card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 8, flexWrap: "wrap" }}>
                    <span style={{ fontWeight: 800, color: "var(--text-primary)" }}>{exam.semester}</span>
                    <span className="badge badge-purple">{exam.academic_year}</span>
                    <span style={{ fontSize: "0.72rem", background: "rgba(251,191,36,0.15)", color: "#fbbf24",
                      border: "1px solid rgba(251,191,36,0.3)", padding: "2px 8px", borderRadius: 999, fontWeight: 600 }}>
                      {exam.subject_codes?.length || 0} subjects
                    </span>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {(exam.subject_codes || []).map(code => (
                      <span key={code} style={{ fontSize: "0.75rem", background: "rgba(124,58,237,0.15)",
                        color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.3)", padding: "2px 8px", borderRadius: 6 }}>
                        {code}
                      </span>
                    ))}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
                    onClick={() => router.push(`/dashboard/batches/${batchId}/exams/${exam.id}`)}
                  ><Pencil size={14} strokeWidth={1.8} /> Enter Marks</button>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: "#fbbf24", borderColor: "rgba(251,191,36,0.3)" }}
                    onClick={() => downloadPdf(exam, "pt1")} disabled={pdfLoading === `${exam.id}-pt1`}>
                    {pdfLoading === `${exam.id}-pt1` ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> PT1</>}
                  </button>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
                    onClick={() => downloadPdf(exam, "pt2")} disabled={pdfLoading === `${exam.id}-pt2`}>
                    {pdfLoading === `${exam.id}-pt2` ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> PT2</>}
                  </button>
                  <button className="btn btn-ghost btn-sm"
                    style={{ color: "#6ee7b7", borderColor: "rgba(16,185,129,0.3)" }}
                    onClick={() => downloadPdf(exam, "semester")} disabled={pdfLoading === `${exam.id}-semester`}>
                    {pdfLoading === `${exam.id}-semester` ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> Sem</>}
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(exam.id)}><Trash2 size={14} strokeWidth={1.8} /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Exam Record?"
          message="This will permanently delete the exam setup and all marks."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
