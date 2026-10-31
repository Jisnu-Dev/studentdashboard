"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { meetings, batches, students as studentsApi } from "@/lib/api";
import { getToken } from "@/lib/auth";

const ROMAN = ["","I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX"];
function toRoman(n) { return ROMAN[n] || String(n); }

const DEFAULT_POINTS = [
  "Student attire – Not following proper student attire",
  "Student attendance percentage (as on date) – Low attendance percentage",
  "Academic progress – Poor academic performance / low internal marks",
  "PS level clearance details – PS levels not completed / Not initiated",
  "Reward Point secured",
  "Support and guidance for slow learners – Requires additional academic support",
  "Support for students with arrear courses – Presence of arrear subjects",
  "Participation in classes and activities – Lack of participation in class activities",
];

const DEFAULT_ACTIONS = [
  "Advised to adhere to proper student attire.",
  "Student advised to improve attendance, daily monitoring and parent informed if no improvement.",
  "Attend remedial classes and complete extra practice assignments.",
  "Complete pending PS levels within the given deadline with mentor support.",
  "Review student reward points periodically.",
  "Follow a daily study schedule and track progress weekly.",
  "Prepare a study plan and attend special coaching classes.",
  "Encourage active participation in class and academic activities.",
];

export default function AttendancePage() {
  const { id: batchId, meetingId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [meeting, setMeeting] = useState(null);
  const [studentList, setStudentList] = useState([]);
  const [records, setRecords] = useState({});   // studentId → { is_present, points_discussed[], action_planned[] }
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [expanded, setExpanded] = useState(null);  // studentId of expanded row

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, m, studs, att] = await Promise.all([
        batches.get(batchId),
        meetings.get(batchId, meetingId),
        studentsApi.list(batchId),
        meetings.getAttendance(batchId, meetingId),
      ]);
      setBatch(b);
      setMeeting(m);
      setStudentList(studs);

      // Build records map: seed all students as absent, then overlay saved data
      const map = {};
      studs.forEach(s => {
        map[s.id] = { is_present: false, points_discussed: [], action_planned: [] };
      });
      att.forEach(a => {
        if (map[a.student_id] !== undefined) {
          map[a.student_id] = {
            is_present: a.is_present,
            points_discussed: a.points_discussed || [],
            action_planned: a.action_planned || [],
          };
        }
      });
      setRecords(map);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [batchId, meetingId]);

  useEffect(() => { load(); }, [load]);

  function togglePresent(studentId) {
    setRecords(r => ({
      ...r,
      [studentId]: { ...r[studentId], is_present: !r[studentId].is_present }
    }));
  }

  function updateField(studentId, field, idx, value) {
    setRecords(r => {
      const arr = [...(r[studentId][field] || [])];
      arr[idx] = value;
      return { ...r, [studentId]: { ...r[studentId], [field]: arr } };
    });
  }

  function addItem(studentId, field) {
    setRecords(r => ({
      ...r,
      [studentId]: { ...r[studentId], [field]: [...(r[studentId][field] || []), ""] }
    }));
  }

  function removeItem(studentId, field, idx) {
    setRecords(r => ({
      ...r,
      [studentId]: { ...r[studentId], [field]: r[studentId][field].filter((_, i) => i !== idx) }
    }));
  }

  function applyDefaults(studentId) {
    setRecords(r => ({
      ...r,
      [studentId]: {
        ...r[studentId],
        points_discussed: [...DEFAULT_POINTS],
        action_planned: [...DEFAULT_ACTIONS],
      }
    }));
  }

  async function handleSave() {
    setSaving(true); setError(""); setSuccess("");
    try {
      const payload = Object.entries(records).map(([sid, rec]) => ({
        student_id: parseInt(sid),
        is_present: rec.is_present,
        points_discussed: rec.points_discussed.filter(p => p.trim()),
        action_planned: rec.action_planned.filter(a => a.trim()),
      }));
      await meetings.saveAttendance(batchId, meetingId, payload);
      setSuccess("Attendance saved!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function downloadMinutes() {
    setPdfLoading(true); setError("");
    try {
      const token = getToken();
      const url = meetings.minutesUrl(batchId, meetingId);
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) {
        const d = await res.json().catch(() => null);
        throw new Error(d?.detail || "PDF failed");
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `minutes_meeting_${toRoman(meeting?.meeting_number)}_${batch?.batch_year}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (e) {
      setError(e.message);
    } finally {
      setPdfLoading(false);
    }
  }

  const presentCount = Object.values(records).filter(r => r.is_present).length;

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
            <Link href={`/dashboard/batches/${batchId}/meetings`}><span>Meetings</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}/meetings/${meetingId}`}>
              <span>Meeting {toRoman(meeting?.meeting_number)}</span>
            </Link>
            <span className="sep">›</span>
            <span className="current">Attendance</span>
          </div>
          <h1>Meeting <span className="gradient-text">Attendance</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
            Meeting {toRoman(meeting?.meeting_number)} · {meeting?.meeting_date} · {presentCount} present
          </p>}
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "var(--success)", borderColor: "var(--success-border)" }}
            onClick={downloadMinutes} disabled={pdfLoading}>
            {pdfLoading ? <span className="spinner" /> : "Minutes PDF"}
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save Attendance"}
          </button>
        </div>
      </div>

      {error   && <div className="alert alert-error"   style={{ marginBottom: 16 }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 16 }}>{success}</div>}

      {/* Quick stats */}
      <div className="stats-row" style={{ marginBottom: 20 }}>
        <div className="card stat-card">
          <div className="stat-value">{studentList.length}</div>
          <div className="stat-label">Total Students</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value" style={{ color: "var(--success)" }}>{presentCount}</div>
          <div className="stat-label">Present</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value" style={{ color: "var(--danger)" }}>{studentList.length - presentCount}</div>
          <div className="stat-label">Absent</div>
        </div>
      </div>

      {/* Student attendance list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {studentList.map((student, idx) => {
          const rec = records[student.id] || { is_present: false, points_discussed: [], action_planned: [] };
          const isExpanded = expanded === student.id;
          return (
            <div key={student.id} className="card"
              style={{
                padding: 0, overflow: "hidden",
                border: rec.is_present ? "1px solid var(--success-border)" : "1px solid var(--glass-border)"
              }}>
              {/* Header row */}
              <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 20px" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", minWidth: 24 }}>{idx + 1}</span>

                {/* Present checkbox */}
                <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", flexShrink: 0 }}>
                  <div
                    onClick={() => togglePresent(student.id)}
                    style={{
                      width: 22, height: 22, borderRadius: 4, border: "2px solid",
                      borderColor: rec.is_present ? "var(--success)" : "var(--text-muted)",
                      background: rec.is_present ? "var(--success-bg)" : "transparent",
                      display: "flex", alignItems: "center", justifyContent: "center",
                      cursor: "pointer", transition: "all 0.15s", flexShrink: 0,
                    }}>
                    {rec.is_present && <span style={{ color: "var(--success)", fontSize: 14, lineHeight: 1 }}>✓</span>}
                  </div>
                </label>

                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, color: "var(--text-primary)" }}>{student.name}</div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>{student.register_number}</div>
                </div>

                {rec.is_present && (
                  <div style={{ display: "flex", gap: 6, alignItems: "center", flexShrink: 0 }}>
                    <span style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>
                      {rec.points_discussed.filter(p=>p.trim()).length} points
                    </span>
                    <button
                      className="btn btn-ghost btn-sm"
                      style={{ fontSize: "0.72rem", padding: "4px 10px" }}
                      onClick={() => setExpanded(isExpanded ? null : student.id)}>
                      {isExpanded ? "▲ Collapse" : "▼ Expand"}
                    </button>
                  </div>
                )}
              </div>

              {/* Expanded details */}
              {isExpanded && rec.is_present && (
                <div style={{
                  borderTop: "1px solid var(--glass-border)",
                  padding: "20px 20px 20px 58px",
                  background: "var(--surface-muted)",
                  display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24,
                }}>
                  {/* Points Discussed */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <label className="form-label" style={{ marginBottom: 0 }}>Points Discussed</label>
                      <div style={{ display: "flex", gap: 6 }}>
                        <button type="button" className="btn btn-ghost btn-sm"
                          style={{ fontSize: "0.68rem", padding: "2px 8px" }}
                          onClick={() => applyDefaults(student.id)}
                          title="Fill with default points">
                          Defaults
                        </button>
                        <button type="button" className="btn btn-ghost btn-sm"
                          style={{ fontSize: "0.68rem", padding: "2px 8px" }}
                          onClick={() => addItem(student.id, "points_discussed")}>
                          + Add
                        </button>
                      </div>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {rec.points_discussed.map((point, pi) => (
                        <div key={pi} style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
                          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", minWidth: 20, paddingTop: 8 }}>
                            {pi + 1}.
                          </span>
                          <textarea
                            className="form-input"
                            value={point}
                            onChange={e => updateField(student.id, "points_discussed", pi, e.target.value)}
                            rows={2}
                            style={{ flex: 1, fontSize: "0.8rem", padding: "6px 8px", resize: "vertical" }}
                          />
                          <button type="button" className="btn btn-danger btn-sm"
                            style={{ marginTop: 4, padding: "4px 8px" }}
                            onClick={() => removeItem(student.id, "points_discussed", pi)}>×</button>
                        </div>
                      ))}
                      {rec.points_discussed.length === 0 && (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontStyle: "italic" }}>
                          No points yet. Click + Add or Defaults.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Action Planned */}
                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
                      <label className="form-label" style={{ marginBottom: 0 }}>Action Planned</label>
                      <button type="button" className="btn btn-ghost btn-sm"
                        style={{ fontSize: "0.68rem", padding: "2px 8px" }}
                        onClick={() => addItem(student.id, "action_planned")}>
                        + Add
                      </button>
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                      {rec.action_planned.map((action, ai) => (
                        <div key={ai} style={{ display: "flex", gap: 6, alignItems: "flex-start" }}>
                          <span style={{ color: "var(--text-muted)", fontSize: "0.8rem", minWidth: 20, paddingTop: 8 }}>
                            {ai + 1}.
                          </span>
                          <textarea
                            className="form-input"
                            value={action}
                            onChange={e => updateField(student.id, "action_planned", ai, e.target.value)}
                            rows={2}
                            style={{ flex: 1, fontSize: "0.8rem", padding: "6px 8px", resize: "vertical" }}
                          />
                          <button type="button" className="btn btn-danger btn-sm"
                            style={{ marginTop: 4, padding: "4px 8px" }}
                            onClick={() => removeItem(student.id, "action_planned", ai)}>×</button>
                        </div>
                      ))}
                      {rec.action_planned.length === 0 && (
                        <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontStyle: "italic" }}>
                          No actions yet. Click + Add.
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Floating save bar */}
      {studentList.length > 0 && (
        <div style={{
          position: "sticky", bottom: 20, marginTop: 24,
          background: "var(--glass-bg)", backdropFilter: "blur(16px)",
          border: "1px solid var(--glass-border)", borderRadius: 12,
          padding: "14px 20px", display: "flex", gap: 12, alignItems: "center",
          justifyContent: "space-between",
        }}>
          <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
            {presentCount} of {studentList.length} students marked present
          </span>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save Attendance"}
          </button>
        </div>
      )}
    </>
  );
}
