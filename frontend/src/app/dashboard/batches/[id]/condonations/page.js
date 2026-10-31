"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, condonations, documents } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, MentorFileHeader, PageSpinner, SEMESTERS, StudentSelect, StudentTag, formGrid } from "@/components/MentorFileParts";
import { FileDown, Plus, Trash2, FileCheck, Download } from "@/lib/icons";

const MIN_ATTENDANCE = 70;      // minimum attendance % to be eligible for condonation
const MAX_PER_STUDENT = 2;      // a student may apply only twice in the entire course
const ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp";

const emptyForm = (batch) => ({
  student_id: "", exam_month_year: "", degree_branch: batch ? `B.E. - ${batch.department}` : "",
  semester: SEMESTERS[0], attendance_percentage: "", reason: "", recommended: true,
});

export default function CondonationsPage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(() => emptyForm(null));
  const [file, setFile] = useState(null);
  const [fileKey, setFileKey] = useState(0);
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState(null);   // "pdf-<id>" | "proof-<id>"
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, items] = await Promise.all([batches.get(batchId), condonations.list(batchId)]);
      setBatch(b);
      setList(items);
      setForm((f) => (f.degree_branch ? f : { ...f, degree_branch: `B.E. - ${b.department}` }));
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const usedByStudent = list.filter((c) => String(c.student_id) === String(form.student_id)).length;
  const limitReached = form.student_id !== "" && usedByStudent >= MAX_PER_STUDENT;
  const belowMinimum = form.attendance_percentage !== "" && Number(form.attendance_percentage) < MIN_ATTENDANCE;

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      let document_id = null;
      if (file) {
        const doc = await documents.upload(batchId, form.student_id,
          { category: "condonation", title: `Condonation proof - ${form.exam_month_year}` }, file);
        document_id = doc.id;
      }
      await condonations.create(batchId, {
        ...form,
        student_id: Number(form.student_id),
        attendance_percentage: Number(form.attendance_percentage),
        document_id,
      });
      setForm(emptyForm(batch));
      setFile(null);
      setFileKey((k) => k + 1);
      await load();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  async function downloadPdf(c) {
    setBusy(`pdf-${c.id}`); setError("");
    try { await downloadFile(condonations.pdfUrl(batchId, c.id), `condonation_${c.register_number}_${c.exam_month_year}.pdf`); }
    catch (e) { setError(e.message); }
    finally { setBusy(null); }
  }

  async function downloadProof(c) {
    setBusy(`proof-${c.id}`); setError("");
    try { await downloadFile(documents.downloadUrl(batchId, c.document_id), `condonation_proof_${c.register_number}`); }
    catch (e) { setError(e.message); }
    finally { setBusy(null); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await condonations.delete(batchId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current="Condonation" title="Condonation" accent="Applications" />

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <form className="card" style={{ padding: 24, marginBottom: 24 }} onSubmit={handleSubmit}>
        <h3 style={{ marginBottom: 6 }}>Application for Condonation</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 18 }}>
          Students short of attendance for medical reasons with at least {MIN_ATTENDANCE}% attendance may apply,
          only twice in the entire course. Attach the approved form with the medical certificate.
        </p>
        <div style={formGrid()}>
          <Field label="Student">
            <StudentSelect students={batch?.students || []} value={form.student_id}
              onChange={(v) => setForm((f) => ({ ...f, student_id: v }))} />
          </Field>
          <Field label="Month & Year of Exam">
            <input className="form-input" placeholder="e.g. Nov 2026" value={form.exam_month_year} onChange={set("exam_month_year")} required />
          </Field>
          <Field label="Degree & Branch">
            <input className="form-input" value={form.degree_branch} onChange={set("degree_branch")} required />
          </Field>
          <Field label="Semester">
            <select className="form-input" value={form.semester} onChange={set("semester")}>
              {SEMESTERS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Attendance %">
            <input className="form-input" type="number" min="0" max="100" step="0.01"
              value={form.attendance_percentage} onChange={set("attendance_percentage")} required />
          </Field>
          <Field label="Recommended">
            <select className="form-input" value={form.recommended ? "yes" : "no"}
              onChange={(e) => setForm((f) => ({ ...f, recommended: e.target.value === "yes" }))}>
              <option value="yes">Yes</option>
              <option value="no">No</option>
            </select>
          </Field>
          <Field label="Reason for Absence">
            <input className="form-input" value={form.reason} onChange={set("reason")} required />
          </Field>
          <Field label="Approved form / medical certificate (optional)">
            <input key={fileKey} className="form-input" type="file" accept={ACCEPT}
              onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </Field>
        </div>

        {limitReached && (
          <div className="alert alert-error" style={{ marginTop: 16 }}>
            This student has already applied for condonation twice and cannot apply again.
          </div>
        )}
        {belowMinimum && (
          <div className="alert alert-error" style={{ marginTop: 16 }}>
            Attendance is below {MIN_ATTENDANCE}% — the student is not eligible for condonation as per the regulations.
          </div>
        )}

        <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={saving || limitReached}>
          {saving ? <span className="spinner" /> : <><Plus size={15} strokeWidth={2} /> Add Application</>}
        </button>
      </form>

      {list.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><FileCheck size={40} strokeWidth={1.2} /></div>
          <h3>No condonation applications</h3>
          <p>Record an application here when a student submits a condonation form.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper" style={{ border: "none", borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Exam</th>
                  <th>Semester</th>
                  <th>Attendance %</th>
                  <th>Reason for Absence</th>
                  <th>Recommended</th>
                  <th style={{ width: 150, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {list.map((c) => (
                  <tr key={c.id}>
                    <td><div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}><StudentTag record={c} /></div></td>
                    <td>{c.exam_month_year}</td>
                    <td>{c.semester}</td>
                    <td>{c.attendance_percentage}</td>
                    <td style={{ color: "var(--text-secondary)" }}>{c.reason}</td>
                    <td>{c.recommended ? "Yes" : "No"}</td>
                    <td>
                      <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                        <button className="btn btn-ghost btn-sm" style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
                          onClick={() => downloadPdf(c)} disabled={busy === `pdf-${c.id}`}>
                          {busy === `pdf-${c.id}` ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> Form</>}
                        </button>
                        {c.document_id && (
                          <button className="btn btn-ghost btn-sm" title="Download attached proof"
                            onClick={() => downloadProof(c)} disabled={busy === `proof-${c.id}`}>
                            {busy === `proof-${c.id}` ? <span className="spinner" /> : <Download size={14} strokeWidth={1.8} />}
                          </button>
                        )}
                        <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(c.id)}>
                          <Trash2 size={14} strokeWidth={1.8} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Application?"
          message="This will permanently delete this condonation record and its attached proof."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
