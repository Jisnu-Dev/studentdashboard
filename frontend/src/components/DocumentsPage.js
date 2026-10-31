"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, documents } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, MentorFileHeader, PageSpinner, StudentSelect, StudentTag, formGrid } from "@/components/MentorFileParts";
import { Upload, Download, Trash2, FolderOpen } from "@/lib/icons";

const ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx";

// Upload + list page for one document category ("personal_details" | "medical_leave").
export default function DocumentsPage({ category, current, title, accent, hint, defaultTitle, withDates }) {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState({ student_id: "", title: defaultTitle, notes: "", from_date: "", to_date: "" });
  const [file, setFile] = useState(null);
  const [fileKey, setFileKey] = useState(0);
  const [saving, setSaving] = useState(false);
  const [downloading, setDownloading] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, list] = await Promise.all([batches.get(batchId), documents.list(batchId, category)]);
      setBatch(b);
      setDocs(list);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId, category]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleUpload(e) {
    e.preventDefault();
    if (!file) { setError("Choose a file to upload"); return; }
    setSaving(true); setError("");
    try {
      const { student_id, ...fields } = form;
      await documents.upload(batchId, student_id, { category, ...fields }, file);
      setForm((f) => ({ ...f, student_id: "", notes: "", from_date: "", to_date: "" }));
      setFile(null);
      setFileKey((k) => k + 1);
      await load();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  async function handleDownload(doc) {
    setDownloading(doc.id); setError("");
    try { await downloadFile(documents.downloadUrl(batchId, doc.id), doc.file_name); }
    catch (e) { setError(e.message); }
    finally { setDownloading(null); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await documents.delete(batchId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;

  const students = batch?.students || [];
  const covered = new Set(docs.map((d) => d.student_id)).size;

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current={current} title={title} accent={accent} />

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{docs.length}</div>
          <div className="stat-label">Files Uploaded</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{covered} / {students.length}</div>
          <div className="stat-label">Students Covered</div>
        </div>
      </div>

      <form className="card" style={{ padding: 24, marginBottom: 24 }} onSubmit={handleUpload}>
        <h3 style={{ marginBottom: 6 }}>Upload</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 18 }}>{hint}</p>
        <div style={formGrid()}>
          <Field label="Student">
            <StudentSelect students={students} value={form.student_id}
              onChange={(v) => setForm((f) => ({ ...f, student_id: v }))} />
          </Field>
          <Field label="Title">
            <input className="form-input" value={form.title} onChange={set("title")} required />
          </Field>
          {withDates && (
            <>
              <Field label="Leave From">
                <input className="form-input" type="date" value={form.from_date} onChange={set("from_date")} required />
              </Field>
              <Field label="Leave To">
                <input className="form-input" type="date" value={form.to_date} min={form.from_date} onChange={set("to_date")} required />
              </Field>
            </>
          )}
          <Field label={withDates ? "Health Issue / Reason" : "Notes (optional)"}>
            <input className="form-input" value={form.notes} onChange={set("notes")} required={withDates} />
          </Field>
          <Field label="File (PDF, image or Word — max 10 MB)">
            <input key={fileKey} className="form-input" type="file" accept={ACCEPT}
              onChange={(e) => setFile(e.target.files?.[0] || null)} required />
          </Field>
        </div>
        <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={saving}>
          {saving ? <span className="spinner" /> : <><Upload size={15} strokeWidth={1.8} /> Upload</>}
        </button>
      </form>

      {docs.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><FolderOpen size={40} strokeWidth={1.2} /></div>
          <h3>Nothing uploaded yet</h3>
          <p>Use the form above to add the first file.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper" style={{ border: "none", borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Title</th>
                  {withDates && <th>Leave Period</th>}
                  <th>{withDates ? "Reason" : "Notes"}</th>
                  <th>File</th>
                  <th style={{ width: 110, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <tr key={d.id}>
                    <td><div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}><StudentTag record={d} /></div></td>
                    <td>{d.title}</td>
                    {withDates && <td>{d.from_date} → {d.to_date}</td>}
                    <td style={{ color: "var(--text-secondary)" }}>{d.notes || "—"}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.8rem" }}>
                      {d.file_name} · {Math.max(1, Math.round(d.file_size / 1024))} KB
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                        <button className="btn btn-ghost btn-sm" onClick={() => handleDownload(d)} disabled={downloading === d.id}>
                          {downloading === d.id ? <span className="spinner" /> : <Download size={14} strokeWidth={1.8} />}
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(d.id)}>
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
          title="Delete File?"
          message="This will permanently delete the uploaded file."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
