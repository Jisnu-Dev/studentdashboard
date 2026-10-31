"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { meetings, batches } from "@/lib/api";
import { getToken } from "@/lib/auth";
import ConfirmModal from "@/components/ConfirmModal";

const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
  "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"];

function toRoman(n) { return ROMAN[n] || String(n); }

export default function MeetingsListPage() {
  const { id: batchId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [meetingList, setMeetingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, list] = await Promise.all([batches.get(batchId), meetings.list(batchId)]);
      setBatch(b);
      setMeetingList(list);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  async function downloadPdf(meeting, type) {
    setPdfLoading(`${meeting.id}-${type}`);
    try {
      const token = getToken();
      const url = type === "circular"
        ? meetings.circularUrl(batchId, meeting.id)
        : meetings.minutesUrl(batchId, meeting.id);
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "PDF failed");
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${type}_meeting_${toRoman(meeting.meeting_number)}_${batch?.batch_year}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(e.message);
    } finally {
      setPdfLoading(null);
    }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try {
      await meetings.delete(batchId, id);
      await load();
    } finally {
      setDeleteLoading(false);
      setConfirmDelete(null);
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
            <span className="current">Meetings</span>
          </div>
          <h1>Mentor-Mentee <span className="gradient-text">Meetings</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
        <Link href={`/dashboard/batches/${batchId}/meetings/new`} className="btn btn-primary">
          + Schedule Meeting
        </Link>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{meetingList.length}</div>
          <div className="stat-label">Total Meetings</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{meetingList.filter(m => m.minutes_text).length}</div>
          <div className="stat-label">With Minutes</div>
        </div>
      </div>

      {meetingList.length === 0 ? (
        <div className="card empty-state">
          <h3>No meetings scheduled</h3>
          <p style={{ marginBottom: 24 }}>Schedule the first mentor-mentee meeting for this batch.</p>
          <Link href={`/dashboard/batches/${batchId}/meetings/new`} className="btn btn-primary">
            + Schedule Meeting
          </Link>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {meetingList.map((m) => (
            <div key={m.id} className="card" style={{ padding: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 12 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10, flexWrap: "wrap" }}>
                    <span style={{ fontSize: "1.1rem", fontWeight: 800, color: "var(--text-primary)" }}>
                      Meeting {toRoman(m.meeting_number)}
                    </span>
                    <span className="badge badge-purple">{m.meeting_date}</span>
                    {m.minutes_text && (
                      <span style={{ fontSize: "0.7rem", background: "var(--success-bg)", color: "var(--success)", border: "1px solid var(--success-border)", padding: "2px 8px", borderRadius: 999, fontWeight: 600 }}>
                        ✓ Minutes recorded
                      </span>
                    )}
                  </div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "4px 24px" }}>
                    <InfoRow label="Time" value={m.meeting_time} />
                    <InfoRow label="Location" value={m.location} />
                    <InfoRow label="Semester" value={m.semester} />
                    <InfoRow label="Agenda items" value={`${m.agenda_items?.length || 0} items`} />
                  </div>
                </div>
                <div style={{ display: "flex", gap: 8, flexShrink: 0, flexWrap: "wrap" }}>
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
                    onClick={() => downloadPdf(m, "circular")}
                    disabled={pdfLoading === `${m.id}-circular`}
                  >
                    {pdfLoading === `${m.id}-circular` ? <span className="spinner" /> : "Circular"}
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    style={{ color: m.minutes_text ? "var(--success)" : "var(--text-muted)", borderColor: m.minutes_text ? "var(--success-border)" : "var(--glass-border)" }}
                    onClick={() => m.minutes_text ? downloadPdf(m, "minutes") : router.push(`/dashboard/batches/${batchId}/meetings/${m.id}`)}
                    disabled={pdfLoading === `${m.id}-minutes`}
                  >
                    {pdfLoading === `${m.id}-minutes` ? <span className="spinner" /> : m.minutes_text ? "Minutes" : "Add Minutes"}
                  </button>
                  <button className="btn btn-ghost btn-sm"
                    onClick={() => router.push(`/dashboard/batches/${batchId}/meetings/${m.id}`)}>
                    Edit
                  </button>
                  <button className="btn btn-danger btn-sm"
                    onClick={() => setConfirmDelete(m.id)}>
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
          title="Delete Meeting?"
          message="This will permanently delete the meeting, its circular, and any recorded minutes."
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
      <span style={{ color: "var(--text-muted)", minWidth: 90 }}>{label}:</span>
      <span style={{ color: "var(--text-primary)", fontWeight: 500 }}>{value}</span>
    </div>
  );
}
