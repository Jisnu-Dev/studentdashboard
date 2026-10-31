"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { counseling, batches } from "@/lib/api";
import { getToken } from "@/lib/auth";
import ConfirmModal from "@/components/ConfirmModal";

export default function CounselingListPage() {
  const { id: batchId, studentId } = useParams();
  const router = useRouter();

  const [sessions, setSessions] = useState([]);
  const [student, setStudent] = useState(null);
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const b = await batches.get(batchId);
      setBatch(b);
      const s = b.students?.find((s) => String(s.id) === String(studentId));
      setStudent(s || null);
      const list = await counseling.list(batchId, studentId);
      setSessions(list);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [batchId, studentId]);

  useEffect(() => { load(); }, [load]);

  async function handleDelete(sessionId) {
    setDeleteLoading(true);
    try {
      await counseling.delete(batchId, studentId, sessionId);
      await load();
    } finally {
      setDeleteLoading(false);
      setConfirmDelete(null);
    }
  }

  async function handlePdfDownload(session) {
    setPdfLoading(session.id);
    try {
      const token = getToken();
      const res = await fetch(counseling.pdfUrl(batchId, studentId, session.id), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `counseling_${student?.register_number}_${session.counseling_date}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    } finally {
      setPdfLoading(null);
    }
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
            <span className="current">{student?.name || "Student"} — Counseling</span>
          </div>
          <h1>
            <span className="gradient-text">Counseling</span> Records
          </h1>
          {student && (
            <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
              {student.register_number} — {student.name}
            </p>
          )}
        </div>
        <Link
          href={`/dashboard/batches/${batchId}/students/${studentId}/counseling/new`}
          className="btn btn-primary"
        >
          + New Session
        </Link>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      {sessions.length === 0 ? (
        <div className="card empty-state">
          <h3>No counseling sessions yet</h3>
          <p style={{ marginBottom: 24 }}>Record the first session for this student.</p>
          <Link
            href={`/dashboard/batches/${batchId}/students/${studentId}/counseling/new`}
            className="btn btn-primary"
          >
            + New Session
          </Link>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {sessions.map((s) => (
            <div key={s.id} className="card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
                    <span className="badge badge-purple">{s.counseling_date}</span>
                    <span style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      AY: {s.academic_year}
                    </span>
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px 24px" }}>
                    <InfoRow label="Initiated by" value={s.reason_initiated_by} />
                    <InfoRow label="Attendance" value={s.attendance_status} />
                    <InfoRow label="Discipline" value={s.discipline_status} />
                    <InfoRow label="Attitude" value={s.attitude_status} />
                    <InfoRow label="Difficulty" value={s.difficulty_meeting_demands ? "Yes" : "No"} />
                    <InfoRow label="Corrective Action" value={s.corrective_action_needed ? "Yes" : "No"} />
                    <InfoRow label="Next Session" value={s.next_session_needed ? "Needed" : "Not Needed"} />
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
                    onClick={() => handlePdfDownload(s)}
                    disabled={pdfLoading === s.id}
                  >
                    {pdfLoading === s.id ? <span className="spinner" /> : "PDF"}
                  </button>
                  <button
                    className="btn btn-danger btn-sm"
                    onClick={() => setConfirmDelete(s.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Session?"
          message="This will permanently delete this counseling session and its PDF."
          danger
          loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}

function InfoRow({ label, value }) {
  return (
    <div style={{ display: "flex", gap: 6, fontSize: "0.8rem" }}>
      <span style={{ color: "var(--text-muted)", minWidth: 110 }}>{label}:</span>
      <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{value}</span>
    </div>
  );
}
