"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { meetings, batches } from "@/lib/api";

function today() { return new Date().toISOString().split("T")[0]; }

const DEFAULT_AGENDA = [
  "Discussion about academic activities.",
  "Discussion about participating in different events.",
  "Any other matter.",
];

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

export default function NewMeetingPage() {
  const { id: batchId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    meeting_date: today(),
    meeting_time: "3.30 PM",
    location: "Department conference hall",
    semester: "I Year - Semester I",
    academic_year: "",
    year_of_study: "I Year",
    agenda_items: [...DEFAULT_AGENDA],
  });

  useEffect(() => {
    batches.get(batchId).then(setBatch).catch((e) => setError(e.message));
  }, [batchId]);

  const setF = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  const setE = (k) => (e) => setF(k)(e.target.value);

  function updateAgendaItem(idx, value) {
    setForm((f) => {
      const items = [...f.agenda_items];
      items[idx] = value;
      return { ...f, agenda_items: items };
    });
  }

  function addAgendaItem() {
    setForm((f) => ({ ...f, agenda_items: [...f.agenda_items, ""] }));
  }

  function removeAgendaItem(idx) {
    setForm((f) => ({ ...f, agenda_items: f.agenda_items.filter((_, i) => i !== idx) }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = {
        ...form,
        agenda_items: form.agenda_items.filter((a) => a.trim()),
      };
      const meeting = await meetings.create(batchId, payload);
      router.push(`/dashboard/batches/${batchId}/meetings`);
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
            <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}/meetings`}><span>Meetings</span></Link>
            <span className="sep">›</span>
            <span className="current">Schedule</span>
          </div>
          <h1>Schedule <span className="gradient-text">New Meeting</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ maxWidth: 680 }}>
        {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

        {/* Meeting details */}
        <div className="card" style={{ padding: 28, marginBottom: 20 }}>
          <h3 style={{ marginBottom: 20, fontSize: "1rem" }}>Meeting Details</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Date</label>
                <input className="form-input" type="date" value={form.meeting_date}
                  onChange={setE("meeting_date")} required />
              </div>
              <div className="form-group">
                <label className="form-label">Time</label>
                <input className="form-input" type="text" placeholder="e.g. 3.30 PM"
                  value={form.meeting_time} onChange={setE("meeting_time")} required />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Location / Venue</label>
              <input className="form-input" type="text"
                placeholder="e.g. Department conference hall"
                value={form.location} onChange={setE("location")} required />
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
                  {["I Year","II Year","III Year","IV Year"].map(y => (
                    <option key={y} value={y} style={{ background: "var(--bg-surface)" }}>{y}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Year &amp; Semester</label>
              <select className="form-input" value={form.semester}
                onChange={setE("semester")} style={{ cursor: "pointer" }}>
                {SEMESTERS.map((s) => (
                  <option key={s} value={s} style={{ background: "var(--bg-surface)" }}>{s}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Agenda items */}
        <div className="card" style={{ padding: 28, marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <h3 style={{ fontSize: "1rem" }}>Agenda Items</h3>
            <button type="button" className="btn btn-ghost btn-sm" onClick={addAgendaItem}>
              + Add Item
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {form.agenda_items.map((item, idx) => (
              <div key={idx} style={{ display: "flex", gap: 10, alignItems: "center" }}>
                <span style={{ color: "var(--text-muted)", fontSize: "0.85rem", minWidth: 24, textAlign: "right" }}>
                  {idx + 1}.
                </span>
                <input
                  className="form-input"
                  type="text"
                  value={item}
                  onChange={(e) => updateAgendaItem(idx, e.target.value)}
                  placeholder={`Agenda item ${idx + 1}`}
                  style={{ flex: 1 }}
                />
                {form.agenda_items.length > 1 && (
                  <button type="button" className="btn btn-danger btn-sm"
                    onClick={() => removeAgendaItem(idx)} style={{ flexShrink: 0 }}>
                    ×
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: "flex", gap: 12 }}>
          <Link href={`/dashboard/batches/${batchId}/meetings`}
            className="btn btn-ghost" style={{ flex: 1, justifyContent: "center" }}>
            Cancel
          </Link>
          <button type="submit" className="btn btn-primary"
            style={{ flex: 3, justifyContent: "center" }} disabled={loading}>
            {loading ? <span className="spinner" /> : "Schedule Meeting"}
          </button>
        </div>
      </form>
    </>
  );
}
