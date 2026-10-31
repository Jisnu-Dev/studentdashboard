"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { analysis, batches, exams } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, PageSpinner, StudentSelect, StudentTag, formGrid } from "@/components/MentorFileParts";
import { FileDown, BookOpen, GraduationCap, Plus, Trash2 } from "@/lib/icons";

const TABS = [
  { key: "pt1",      label: "PT I",         Icon: BookOpen,      color: "var(--warning)" },
  { key: "pt2",      label: "PT II",        Icon: BookOpen,      color: "var(--accent)" },
  { key: "semester", label: "Semester End", Icon: GraduationCap, color: "var(--success)" },
];

const emptyRemedial = () => ({ student_id: "", subjects: "", action_taken: "", impact: "" });

export default function ResultAnalysisPage() {
  const { id: batchId, examId } = useParams();

  const [batch, setBatch] = useState(null);
  const [setup, setSetup] = useState(null);
  const [tab, setTab] = useState("pt1");
  const [subjects, setSubjects] = useState([]);
  const [details, setDetails] = useState({});   // {code: {name, faculty}}
  const [passMark, setPassMark] = useState(50);
  const [remedial, setRemedial] = useState([]);
  const [remedialForm, setRemedialForm] = useState(emptyRemedial);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [adding, setAdding] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, s, result, actions] = await Promise.all([
        batches.get(batchId),
        exams.get(batchId, examId),
        analysis.get(batchId, examId, tab),
        analysis.listRemedial(batchId, examId),
      ]);
      setBatch(b);
      setSetup(s);
      setSubjects(result.subjects);
      setPassMark(s.pt_pass_mark);
      setRemedial(actions);
      const map = {};
      s.subject_codes.forEach((code) => {
        map[code] = { name: s.subject_details?.[code]?.name || "", faculty: s.subject_details?.[code]?.faculty || "" };
      });
      setDetails(map);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId, examId, tab]);

  useEffect(() => { load(); }, [load]);

  function setDetail(code, key, value) {
    setDetails((d) => ({ ...d, [code]: { ...d[code], [key]: value } }));
  }

  async function saveDetails() {
    await exams.update(batchId, examId, { subject_details: details, pt_pass_mark: Number(passMark) || 0 });
  }

  async function handleSave() {
    setSaving(true); setError(""); setSuccess("");
    try {
      await saveDetails();
      await load();
      setSuccess("Analysis details saved!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }

  async function downloadPdf() {
    setPdfLoading(true); setError("");
    try {
      await saveDetails();   // the PDF is built from saved subject names / faculty / pass mark
      await downloadFile(
        analysis.pdfUrl(batchId, examId, tab),
        `result_analysis_${tab}_${setup?.semester}_${batch?.batch_year}.pdf`,
      );
      await load();
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(false); }
  }

  async function addRemedial(e) {
    e.preventDefault();
    setAdding(true); setError("");
    try {
      await analysis.addRemedial(batchId, examId, {
        ...remedialForm,
        student_id: Number(remedialForm.student_id),
        exam_type: tab,
        subjects: remedialForm.subjects || null,
        impact: remedialForm.impact || null,
      });
      setRemedialForm(emptyRemedial());
      await load();
    } catch (err) { setError(err.message); }
    finally { setAdding(false); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await analysis.deleteRemedial(batchId, examId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;
  if (!setup) return <div className="alert alert-error" style={{ margin: 24 }}>{error || "Exam record not found"}</div>;

  const activeTab = TABS.find((t) => t.key === tab);
  const tabRemedial = remedial.filter((r) => r.exam_type === tab);
  const failures = subjects.filter((s) => s.failed_students.length > 0);
  const set = (k) => (e) => setRemedialForm((f) => ({ ...f, [k]: e.target.value }));

  return (
    <>
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}/exams`}><span>Exams</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}/exams/${examId}`}><span>{setup.semester}</span></Link>
            <span className="sep">›</span>
            <span className="current">Analysis</span>
          </div>
          <h1>Result <span className="gradient-text">Analysis</span></h1>
          <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>{setup.semester} · {setup.academic_year}</p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-ghost" style={{ color: activeTab.color, borderColor: activeTab.color }}
            onClick={downloadPdf} disabled={pdfLoading}>
            {pdfLoading ? <span className="spinner" /> : <><FileDown size={16} strokeWidth={1.8} /> {activeTab.label} Analysis PDF</>}
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save Details"}
          </button>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 20 }}>{success}</div>}

      <div style={{ display: "flex", gap: 10, marginBottom: 20, alignItems: "center", flexWrap: "wrap" }}>
        {TABS.map(({ key, label, Icon, color }) => (
          <button key={key} className="btn btn-ghost btn-sm" onClick={() => setTab(key)}
            style={tab === key ? { color, borderColor: color, background: "var(--surface-muted)" } : {}}>
            <Icon size={15} strokeWidth={1.8} /> {label}
          </button>
        ))}
        {tab !== "semester" && (
          <label style={{ display: "flex", gap: 8, alignItems: "center", marginLeft: "auto", fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            PT pass mark (out of {setup.pt_max_marks})
            <input className="form-input" type="number" min="0" max={setup.pt_max_marks} style={{ width: 90, padding: "6px 10px" }}
              value={passMark} onChange={(e) => setPassMark(e.target.value)} />
          </label>
        )}
      </div>

      {/* Analysis table */}
      <div className="card" style={{ padding: 0, overflow: "hidden", marginBottom: 24 }}>
        <div className="table-wrapper" style={{ border: "none", borderRadius: 0, overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Subject Code</th>
                <th>Subject Name</th>
                <th>Name of Faculty</th>
                <th style={{ textAlign: "center" }}>Attended</th>
                <th style={{ textAlign: "center" }}>Pass</th>
                <th style={{ textAlign: "center" }}>Fail</th>
                <th style={{ textAlign: "center" }}>% Pass</th>
                <th style={{ textAlign: "center" }}>Absent</th>
              </tr>
            </thead>
            <tbody>
              {subjects.map((s) => (
                <tr key={s.subject_code}>
                  <td><span className="badge badge-purple">{s.subject_code}</span></td>
                  <td>
                    <input className="form-input" style={{ minWidth: 200, padding: "6px 10px" }} placeholder="Subject name"
                      value={details[s.subject_code]?.name || ""} onChange={(e) => setDetail(s.subject_code, "name", e.target.value)} />
                  </td>
                  <td>
                    <input className="form-input" style={{ minWidth: 200, padding: "6px 10px" }} placeholder="Faculty name(s)"
                      value={details[s.subject_code]?.faculty || ""} onChange={(e) => setDetail(s.subject_code, "faculty", e.target.value)} />
                  </td>
                  <td style={{ textAlign: "center" }}>{s.attended}</td>
                  <td style={{ textAlign: "center", color: "var(--success)", fontWeight: 600 }}>{s.passed}</td>
                  <td style={{ textAlign: "center", color: s.failed ? "var(--danger)" : "inherit", fontWeight: 600 }}>{s.failed}</td>
                  <td style={{ textAlign: "center", color: "var(--text-primary)", fontWeight: 700 }}>{s.pass_percentage.toFixed(2)}</td>
                  <td style={{ textAlign: "center" }}>{s.absent}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Students who failed */}
      {failures.length > 0 && (
        <div className="card" style={{ padding: 24, marginBottom: 24 }}>
          <h3 style={{ marginBottom: 14 }}>Students Who Failed</h3>
          {failures.map((s) => (
            <div key={s.subject_code} style={{ display: "flex", gap: 10, marginBottom: 8, fontSize: "0.85rem", flexWrap: "wrap" }}>
              <span className="badge badge-purple">{s.subject_code}</span>
              <span style={{ color: "var(--text-secondary)" }}>{s.failed_students.join(" · ")}</span>
            </div>
          ))}
        </div>
      )}

      {/* Remedial actions */}
      <form className="card" style={{ padding: 24, marginBottom: 16 }} onSubmit={addRemedial}>
        <h3 style={{ marginBottom: 6 }}>Remedial Actions — {activeTab.label}</h3>
        <p style={{ color: "var(--text-secondary)", fontSize: "0.85rem", marginBottom: 18 }}>
          Document the remedial action taken for each student who failed or was identified as a slow learner,
          and its impact on their academic performance. These are included in the analysis PDF.
        </p>
        <div style={formGrid(260)}>
          <Field label="Student">
            <StudentSelect students={batch?.students || []} value={remedialForm.student_id}
              onChange={(v) => setRemedialForm((f) => ({ ...f, student_id: v }))} />
          </Field>
          <Field label="Subjects">
            <input className="form-input" placeholder="e.g. CS1001, MA1001" value={remedialForm.subjects} onChange={set("subjects")} />
          </Field>
          <Field label="Remedial Action Taken">
            <textarea className="form-input" rows={2} value={remedialForm.action_taken} onChange={set("action_taken")} required />
          </Field>
          <Field label="Impact on Academic Performance">
            <textarea className="form-input" rows={2} value={remedialForm.impact} onChange={set("impact")} />
          </Field>
        </div>
        <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={adding}>
          {adding ? <span className="spinner" /> : <><Plus size={15} strokeWidth={2} /> Add Remedial Action</>}
        </button>
      </form>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {tabRemedial.map((r) => (
          <div key={r.id} className="card" style={{ padding: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "flex-start" }}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap", marginBottom: 8 }}>
                  <StudentTag record={r} />
                  {r.subjects && <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>{r.subjects}</span>}
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-primary)", whiteSpace: "pre-wrap" }}>{r.action_taken}</div>
                {r.impact && (
                  <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginTop: 4, whiteSpace: "pre-wrap" }}>
                    Impact: {r.impact}
                  </div>
                )}
              </div>
              <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(r.id)}>
                <Trash2 size={14} strokeWidth={1.8} />
              </button>
            </div>
          </div>
        ))}
      </div>

      {confirmDelete && (
        <ConfirmModal
          title="Delete Remedial Action?"
          message="This will permanently delete this remedial action record."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
