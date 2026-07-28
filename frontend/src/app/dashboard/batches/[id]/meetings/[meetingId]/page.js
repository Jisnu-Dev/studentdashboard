"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { meetings, batches } from "@/lib/api";
import { getToken } from "@/lib/auth";

const ROMAN = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
  "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"];
function toRoman(n) { return ROMAN[n] || String(n); }

const SEMESTERS = [
  "I Year - Semester I",
  "I Year - Semester II",
  "II Year - Semester III",
  "II Year - Semester IV",
  "III Year - Semester V",
  "III Year - Semester VI",
  "IV Year - Semester VII",
  "IV Year - Semester VIII",
];

export default function MeetingDetailPage() {
  const { id: batchId, meetingId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [meeting, setMeeting] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Editable fields
  const [form, setForm] = useState(null);
  const [minutesText, setMinutesText] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, m] = await Promise.all([batches.get(batchId), meetings.get(batchId, meetingId)]);
      setBatch(b);
      setMeeting(m);
      setForm({
        meeting_date: m.meeting_date,
        meeting_time: m.meeting_time,
        location: m.location,
        semester: m.semester,
        academic_year: m.academic_year || "",
        year_of_study: m.year_of_study || "",
        agenda_items: [...(m.agenda_items || [])],
      });
      setMinutesText(m.minutes_text || "");
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [batchId, meetingId]);

  useEffect(() => { load(); }, [load]);

  const setF = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  const setE = (k) => (e) => setF(k)(e.target.value);

  function updateAgenda(idx, val) {
    setForm((f) => { const a = [...f.agenda_items]; a[idx] = val; return { ...f, agenda_items: a }; });
  }

  async function handleSave() {
    setSaving(true); setError(""); setSuccess("");
    try {
      await meetings.update(batchId, meetingId, {
        ...form,
        agenda_items: form.agenda_items.filter((a) => a.trim()),
        minutes_text: minutesText || null,
      });
      setSuccess("Saved successfully!");
      await load();
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function downloadPdf(type) {
    setPdfLoading(type);
    try {
      const token = getToken();
      const url = type === "circular"
        ? meetings.circularUrl(batchId, meetingId)
        : meetings.minutesUrl(batchId, meetingId);
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) {
        const data = await res.json().catch(() => null);
        throw new Error(data?.detail || "PDF failed");
      }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${type}_meeting_${toRoman(meeting?.meeting_number)}_${batch?.batch_year}.pdf`;
      a.click();
      URL.revokeObjectURL(a.href);
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
  if (!meeting || !form) return null;

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
            <span className="current">Meeting {toRoman(meeting.meeting_number)}</span>
          </div>
          <h1>Meeting <span className="gradient-text">{toRoman(meeting.meeting_number)}</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#6ee7b7", borderColor: "rgba(16,185,129,0.3)" }}
            onClick={() => router.push(`/dashboard/batches/${batchId}/meetings/${meetingId}/attendance`)}>
            ✅ Attendance
          </button>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
            onClick={() => downloadPdf("circular")} disabled={pdfLoading === "circular"}>
            {pdfLoading === "circular" ? <span className="spinner" /> : "📄 Circular PDF"}
          </button>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#6ee7b7", borderColor: "rgba(16,185,129,0.3)" }}
            onClick={() => downloadPdf("minutes")} disabled={pdfLoading === "minutes"}>
            {pdfLoading === "minutes" ? <span className="spinner" /> : "📄 Minutes PDF"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 16 }}>{success}</div>}

      <div style={{ display: "flex", flexDirection: "column", gap: 20, maxWidth: 720 }}>
        {/* Meeting details */}
        <div className="card" style={{ padding: 28 }}>
          <h3 style={{ marginBottom: 20, fontSize: "1rem" }}>Meeting Details</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Date</label>
                <input className="form-input" type="date" value={form.meeting_date}
                  onChange={setE("meeting_date")} />
              </div>
              <div className="form-group">
                <label className="form-label">Time</label>
                <input className="form-input" type="text" value={form.meeting_time}
                  onChange={setE("meeting_time")} />
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Location</label>
              <input className="form-input" type="text" value={form.location}
                onChange={setE("location")} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Academic Year</label>
                <input className="form-input" type="text" placeholder="e.g. 2025-2026"
                  value={form.academic_year} onChange={setE("academic_year")} />
              </div>
              <div className="form-group">
                <label className="form-label">Year of Study</label>
                <select className="form-input" value={form.year_of_study} onChange={setE("year_of_study")}
                  style={{ cursor: "pointer" }}>
                  <option value="" style={{ background: "#13133a" }}>-- Select --</option>
                  {["I Year","II Year","III Year","IV Year"].map(y => (
                    <option key={y} value={y} style={{ background: "#13133a" }}>{y}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="form-label">Year &amp; Semester</label>
              <select className="form-input" value={form.semester}
                onChange={setE("semester")} style={{ cursor: "pointer" }}>
                {SEMESTERS.map((s) => (
                  <option key={s} value={s} style={{ background: "#13133a" }}>{s}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Agenda */}
        <div className="card" style={{ padding: 28 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontSize: "1rem" }}>Agenda Items</h3>
            <button type="button" className="btn btn-ghost btn-sm"
              onClick={() => setForm((f) => ({ ...f, agenda_items: [...f.agenda_items, ""] }))}>
              + Add
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {form.agenda_items.map((item, idx) => (
              <div key={idx} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem", minWidth: 24, textAlign: "right" }}>{idx + 1}.</span>
                <input className="form-input" type="text" value={item}
                  onChange={(e) => updateAgenda(idx, e.target.value)} style={{ flex: 1 }} />
                {form.agenda_items.length > 1 && (
                  <button type="button" className="btn btn-danger btn-sm"
                    onClick={() => setForm((f) => ({ ...f, agenda_items: f.agenda_items.filter((_, i) => i !== idx) }))}>
                    ✕
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Minutes of meeting */}
        <div className="card" style={{ padding: 28 }}>
          <h3 style={{ marginBottom: 6, fontSize: "1rem" }}>Minutes of Meeting</h3>
          <p style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 16 }}>
            Record what was discussed during the meeting. Each new line will appear as a paragraph in the PDF.
          </p>
          <textarea
            className="form-input"
            value={minutesText}
            onChange={(e) => setMinutesText(e.target.value)}
            placeholder="Enter the minutes of the meeting here...&#10;&#10;Each paragraph on a new line."
            rows={8}
            style={{ resize: "vertical", fontFamily: "Inter, sans-serif", lineHeight: 1.6 }}
          />
        </div>

        {/* Save */}
        <button className="btn btn-primary btn-lg" onClick={handleSave} disabled={saving}
          style={{ justifyContent: "center" }}>
          {saving ? <span className="spinner" /> : "Save Changes"}
        </button>
      </div>
    </>
  );
}
