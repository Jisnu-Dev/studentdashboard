"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, achievements, documents } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, MentorFileHeader, PageSpinner, SEMESTERS, StudentSelect, formGrid } from "@/components/MentorFileParts";
import { FileDown, Plus, Trash2, Trophy, Download } from "@/lib/icons";

const CATEGORIES = [
  "Technical Events",
  "Non-Technical Events",
  "Cultural Events",
  "Sports Events",
  "Social Service Activities",
  "Entrepreneurship and Innovation Activities",
  "Leadership and Personality Development Programs",
  "Placement and Career Development Events",
];
const LEVELS = ["International", "National", "State"];
const RESULTS = [
  "Participation", "Winner", "Runner-Up", "Special Award", "Recognition",
  "Team Achievement", "Event Organizer", "Volunteer", "Certificate of Appreciation",
];
const ACCEPT = ".pdf,.jpg,.jpeg,.png,.webp";

const emptyForm = () => ({
  student_id: "", academic_year: "", semester: SEMESTERS[0], category: CATEGORIES[0],
  event_name: "", level: "National", result: "Participation", event_date: "",
});

export default function AchievementsPage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [form, setForm] = useState(emptyForm);
  const [file, setFile] = useState(null);
  const [fileKey, setFileKey] = useState(0);
  const [saving, setSaving] = useState(false);
  const [busy, setBusy] = useState(null);   // "pdf-<student>-<year>" | "cert-<id>"
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, items] = await Promise.all([batches.get(batchId), achievements.list(batchId)]);
      setBatch(b);
      setList(items);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      let document_id = null;
      if (file) {
        const doc = await documents.upload(batchId, form.student_id,
          { category: "certificate", title: form.event_name }, file);
        document_id = doc.id;
      }
      await achievements.create(batchId, {
        ...form,
        student_id: Number(form.student_id),
        event_date: form.event_date || null,
        document_id,
      });
      // Keep student / year / semester so several certificates can be entered in a row
      setForm((f) => ({ ...f, event_name: "", event_date: "" }));
      setFile(null);
      setFileKey((k) => k + 1);
      await load();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  async function downloadSummary(group) {
    const key = `pdf-${group.student_id}-${group.academic_year}`;
    setBusy(key); setError("");
    try {
      await downloadFile(
        achievements.pdfUrl(batchId, group.student_id, group.academic_year),
        `achievements_${group.register_number}_${group.academic_year}.pdf`,
      );
    } catch (e) { setError(e.message); }
    finally { setBusy(null); }
  }

  async function downloadCertificate(a) {
    setBusy(`cert-${a.id}`); setError("");
    try { await downloadFile(documents.downloadUrl(batchId, a.document_id), `certificate_${a.register_number}_${a.event_name}`); }
    catch (e) { setError(e.message); }
    finally { setBusy(null); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await achievements.delete(batchId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;

  // One summary sheet per student per academic year
  const groups = [];
  list.forEach((a) => {
    let g = groups.find((x) => x.student_id === a.student_id && x.academic_year === a.academic_year);
    if (!g) {
      g = { student_id: a.student_id, academic_year: a.academic_year, student_name: a.student_name,
            register_number: a.register_number, items: [] };
      groups.push(g);
    }
    g.items.push(a);
  });

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current="Achievements" title="Student" accent="Achievements" />

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <form className="card" style={{ padding: 24, marginBottom: 24 }} onSubmit={handleSubmit}>
        <h3 style={{ marginBottom: 6 }}>Add Achievement</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 18 }}>
          Collect the certificate from the student (or download it from the BIP portal) and attach it here.
        </p>
        <div style={formGrid()}>
          <Field label="Student">
            <StudentSelect students={batch?.students || []} value={form.student_id}
              onChange={(v) => setForm((f) => ({ ...f, student_id: v }))} />
          </Field>
          <Field label="Academic Year">
            <input className="form-input" placeholder="e.g. 2025-2026" value={form.academic_year} onChange={set("academic_year")} required />
          </Field>
          <Field label="Semester">
            <select className="form-input" value={form.semester} onChange={set("semester")}>
              {SEMESTERS.map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Field label="Event Category">
            <select className="form-input" value={form.category} onChange={set("category")}>
              {CATEGORIES.map((c) => <option key={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Event Name">
            <input className="form-input" value={form.event_name} onChange={set("event_name")} required />
          </Field>
          <Field label="International / National / State">
            <select className="form-input" value={form.level} onChange={set("level")}>
              {LEVELS.map((l) => <option key={l}>{l}</option>)}
            </select>
          </Field>
          <Field label="Participation / Award">
            <select className="form-input" value={form.result} onChange={set("result")}>
              {RESULTS.map((r) => <option key={r}>{r}</option>)}
            </select>
          </Field>
          <Field label="Event Date (optional)">
            <input className="form-input" type="date" value={form.event_date} onChange={set("event_date")} />
          </Field>
          <Field label="Certificate (PDF or image, optional)">
            <input key={fileKey} className="form-input" type="file" accept={ACCEPT}
              onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </Field>
        </div>
        <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={saving}>
          {saving ? <span className="spinner" /> : <><Plus size={15} strokeWidth={2} /> Add Achievement</>}
        </button>
      </form>

      {groups.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><Trophy size={40} strokeWidth={1.2} /></div>
          <h3>No achievements recorded yet</h3>
          <p>Add a student&apos;s event participation or award using the form above.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {groups.map((g) => {
            const key = `pdf-${g.student_id}-${g.academic_year}`;
            return (
              <div key={key} className="card" style={{ padding: 0, overflow: "hidden" }}>
                <div style={{ padding: "16px 24px", borderBottom: "1px solid var(--glass-border)", display: "flex",
                  justifyContent: "space-between", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                    <span className="badge badge-purple">{g.register_number}</span>
                    <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{g.student_name}</span>
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>AY {g.academic_year}</span>
                  </div>
                  <button className="btn btn-ghost btn-sm" style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
                    onClick={() => downloadSummary(g)} disabled={busy === key}>
                    {busy === key ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> Summary Sheet</>}
                  </button>
                </div>
                <div className="table-wrapper" style={{ border: "none", borderRadius: 0 }}>
                  <table>
                    <thead>
                      <tr>
                        <th style={{ width: 60 }}>S.NO</th>
                        <th>Event Name</th>
                        <th>Category</th>
                        <th>Semester</th>
                        <th>Level</th>
                        <th>Participation / Award</th>
                        <th style={{ width: 110, textAlign: "right" }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {g.items.map((a, idx) => (
                        <tr key={a.id}>
                          <td style={{ color: "var(--text-muted)", textAlign: "center" }}>{idx + 1}</td>
                          <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>{a.event_name}</td>
                          <td>{a.category}</td>
                          <td>{a.semester || "—"}</td>
                          <td>{a.level}</td>
                          <td>{a.result}</td>
                          <td>
                            <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                              {a.document_id && (
                                <button className="btn btn-ghost btn-sm" title="Download certificate"
                                  onClick={() => downloadCertificate(a)} disabled={busy === `cert-${a.id}`}>
                                  {busy === `cert-${a.id}` ? <span className="spinner" /> : <Download size={14} strokeWidth={1.8} />}
                                </button>
                              )}
                              <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(a.id)}>
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
            );
          })}
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Achievement?"
          message="This will permanently delete this achievement and its certificate."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
