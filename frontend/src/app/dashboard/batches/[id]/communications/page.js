"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, communications } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, MentorFileHeader, PageSpinner, StudentSelect, StudentTag, formGrid } from "@/components/MentorFileParts";
import { FileDown, Plus, Trash2, Phone } from "@/lib/icons";

const CONTACTS = ["Student", "Father", "Mother", "Guardian"];
const MODES = ["Phone", "In Person", "Message", "Email"];

const today = () => new Date().toISOString().slice(0, 10);
const emptyForm = () => ({
  student_id: "", communication_date: today(), contact_person: "Father", mode: "Phone",
  details: "", feedback: "", action_taken: "",
});

export default function CommunicationsPage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, list] = await Promise.all([batches.get(batchId), communications.list(batchId)]);
      setBatch(b);
      setRecords(list);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      await communications.create(batchId, {
        ...form,
        student_id: Number(form.student_id),
        feedback: form.feedback || null,
        action_taken: form.action_taken || null,
      });
      setForm(emptyForm());
      await load();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  async function downloadPdf() {
    setPdfLoading(true); setError("");
    try { await downloadFile(communications.pdfUrl(batchId), `mentor_note_${batch?.batch_year}.pdf`); }
    catch (e) { setError(e.message); }
    finally { setPdfLoading(false); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await communications.delete(batchId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current="Mentor Note" title="Mentor" accent="Note">
        <button className="btn btn-primary" onClick={downloadPdf} disabled={pdfLoading || records.length === 0}>
          {pdfLoading ? <span className="spinner" /> : <><FileDown size={16} strokeWidth={1.8} /> Mentor Note PDF</>}
        </button>
      </MentorFileHeader>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <form className="card" style={{ padding: 24, marginBottom: 24 }} onSubmit={handleSubmit}>
        <h3 style={{ marginBottom: 6 }}>Record a Communication</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 18 }}>
          Record every communication with a student or parent — who it was with, the date, what was communicated,
          the feedback received and the action taken.
        </p>
        <div style={formGrid()}>
          <Field label="Student">
            <StudentSelect students={batch?.students || []} value={form.student_id}
              onChange={(v) => setForm((f) => ({ ...f, student_id: v }))} />
          </Field>
          <Field label="Date of Communication">
            <input className="form-input" type="date" value={form.communication_date} onChange={set("communication_date")} required />
          </Field>
          <Field label="Communicated With">
            <select className="form-input" value={form.contact_person} onChange={set("contact_person")}>
              {CONTACTS.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Mode">
            <select className="form-input" value={form.mode} onChange={set("mode")}>
              {MODES.map((m) => <option key={m}>{m}</option>)}
            </select>
          </Field>
        </div>
        <div style={{ ...formGrid(280), marginTop: 16 }}>
          <Field label="Details of the Information Communicated">
            <textarea className="form-input" rows={3} value={form.details} onChange={set("details")} required />
          </Field>
          <Field label="Feedback Received">
            <textarea className="form-input" rows={3} value={form.feedback} onChange={set("feedback")} />
          </Field>
          <Field label="Action Taken Based on the Feedback">
            <textarea className="form-input" rows={3} value={form.action_taken} onChange={set("action_taken")} />
          </Field>
        </div>
        <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={saving}>
          {saving ? <span className="spinner" /> : <><Plus size={15} strokeWidth={2} /> Add Record</>}
        </button>
      </form>

      {records.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><Phone size={40} strokeWidth={1.2} /></div>
          <h3>No communication records yet</h3>
          <p>Add the first record using the form above.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {records.map((r) => (
            <div key={r.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 10 }}>
                    <StudentTag record={r} />
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                      {r.communication_date} · {r.contact_person}{r.mode ? ` · ${r.mode}` : ""}
                    </span>
                  </div>
                  <Line label="Details" value={r.details} />
                  <Line label="Feedback" value={r.feedback} />
                  <Line label="Action taken" value={r.action_taken} />
                </div>
                <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(r.id)}>
                  <Trash2 size={14} strokeWidth={1.8} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Record?"
          message="This will permanently delete this communication record."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}

function Line({ label, value }) {
  if (!value) return null;
  return (
    <div style={{ display: "flex", gap: 6, fontSize: "0.85rem", marginBottom: 4 }}>
      <span style={{ color: "var(--text-muted)", minWidth: 100 }}>{label}:</span>
      <span style={{ color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{value}</span>
    </div>
  );
}
