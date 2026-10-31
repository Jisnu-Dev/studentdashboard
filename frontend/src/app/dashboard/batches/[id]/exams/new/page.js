"use client";
import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { exams, batches } from "@/lib/api";
import MaxMarksField from "@/components/MaxMarksField";

const SEMESTERS = [
  "I Year - Semester I", "I Year - Semester II",
  "II Year - Semester III", "II Year - Semester IV",
  "III Year - Semester V", "III Year - Semester VI",
  "IV Year - Semester VII", "IV Year - Semester VIII",
];

function currentAcademicYear() {
  const now = new Date();
  const y = now.getFullYear();
  return now.getMonth() >= 6 ? `${y}-${y + 1}` : `${y - 1}-${y}`;
}

export default function NewExamPage() {
  const { id: batchId } = useParams();
  const router = useRouter();
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [form, setForm] = useState({
    semester: "I Year - Semester I",
    academic_year: currentAcademicYear(),
    subject_codes: [""],
    pt_max_marks: "100",
  });

  useEffect(() => { batches.get(batchId).then(setBatch).catch(e => setError(e.message)); }, [batchId]);

  const setE = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  function updateCode(idx, val) {
    setForm(f => { const a = [...f.subject_codes]; a[idx] = val.toUpperCase(); return { ...f, subject_codes: a }; });
  }
  function addCode() { setForm(f => ({ ...f, subject_codes: [...f.subject_codes, ""] })); }
  function removeCode(idx) { setForm(f => ({ ...f, subject_codes: f.subject_codes.filter((_, i) => i !== idx) })); }

  async function handleSubmit(e) {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const payload = {
        ...form,
        subject_codes: form.subject_codes.filter(c => c.trim()),
        pt_max_marks: Number(form.pt_max_marks),
      };
      if (payload.subject_codes.length === 0) throw new Error("Add at least one subject code");
      if (!Number.isInteger(payload.pt_max_marks) || payload.pt_max_marks < 1) throw new Error("Enter the maximum marks for the periodical tests");
      const exam = await exams.create(batchId, payload);
      router.push(`/dashboard/batches/${batchId}/exams/${exam.id}`);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
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
            <Link href={`/dashboard/batches/${batchId}/exams`}><span>Exams</span></Link>
            <span className="sep">›</span>
            <span className="current">Setup</span>
          </div>
          <h1>Setup <span className="gradient-text">Exam Record</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ maxWidth: 600 }}>
        {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

        <div className="card" style={{ padding: 28, marginBottom: 20 }}>
          <h3 style={{ marginBottom: 20, fontSize: "1rem" }}>Exam Details</h3>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div className="form-group">
                <label className="form-label">Academic Year</label>
                <input className="form-input" type="text" placeholder="e.g. 2024-2025"
                  value={form.academic_year} onChange={setE("academic_year")} required />
              </div>
              <div className="form-group">
                <label className="form-label">Semester</label>
                <select className="form-input" value={form.semester} onChange={setE("semester")} style={{ cursor: "pointer" }}>
                  {SEMESTERS.map(s => <option key={s} value={s} style={{ background: "var(--bg-surface)" }}>{s}</option>)}
                </select>
              </div>
            </div>
            <MaxMarksField value={form.pt_max_marks} onChange={v => setForm(f => ({ ...f, pt_max_marks: v }))} />
          </div>
        </div>

        <div className="card" style={{ padding: 28, marginBottom: 20 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <h3 style={{ fontSize: "1rem", marginBottom: 4 }}>Subject Codes</h3>
              <p style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Add the subject codes for this semester (e.g. CS1001, MA1002)
              </p>
            </div>
            <button type="button" className="btn btn-ghost btn-sm" onClick={addCode}>+ Add</button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            {form.subject_codes.map((code, idx) => (
              <div key={idx} style={{ display: "flex", gap: 8 }}>
                <input className="form-input" type="text" value={code} placeholder={`Subject ${idx + 1}`}
                  onChange={e => updateCode(idx, e.target.value)}
                  style={{ flex: 1, fontFamily: "monospace", letterSpacing: "0.05em" }} />
                {form.subject_codes.length > 1 && (
                  <button type="button" className="btn btn-danger btn-sm" onClick={() => removeCode(idx)}>×</button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", gap: 12 }}>
          <Link href={`/dashboard/batches/${batchId}/exams`}
            className="btn btn-ghost" style={{ flex: 1, justifyContent: "center" }}>Cancel</Link>
          <button type="submit" className="btn btn-primary" style={{ flex: 3, justifyContent: "center" }} disabled={loading}>
            {loading ? <span className="spinner" /> : "Create & Enter Marks →"}
          </button>
        </div>
      </form>
    </>
  );
}
