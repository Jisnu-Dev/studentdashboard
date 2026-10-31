"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, semesterResults } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import { MentorFileHeader, PageSpinner } from "@/components/MentorFileParts";
import { FileDown, GraduationCap, AlertCircle, Users } from "@/lib/icons";

const SEMESTER_KEYS = ["1", "2", "3", "4", "5", "6", "7", "8"];

const TABS = [
  { key: "gpa",     label: "GPA & CGPA",     Icon: GraduationCap, color: "var(--success)" },
  { key: "arrears", label: "Arrear Details", Icon: AlertCircle,   color: "var(--warning)" },
];

const cellInput = { width: 64, padding: "6px 8px", textAlign: "center" };

export default function SemesterResultsPage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [rows, setRows] = useState({});   // {studentId: {gpa: {"1": val}, arrears: {"1": val}, cgpa}}
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [tab, setTab] = useState("gpa");
  const [academicYear, setAcademicYear] = useState("");

  const load = useCallback(async () => {
    try {
      const [b, saved] = await Promise.all([batches.get(batchId), semesterResults.list(batchId)]);
      setBatch(b);
      const map = {};
      (b.students || []).forEach((st) => { map[st.id] = { gpa: {}, arrears: {}, cgpa: "" }; });
      saved.forEach((rec) => {
        if (map[rec.student_id]) {
          map[rec.student_id] = { gpa: rec.gpa || {}, arrears: rec.arrears || {}, cgpa: rec.cgpa || "" };
        }
      });
      setRows(map);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  function setValue(studentId, type, sem, value) {
    setRows((r) => ({
      ...r,
      [studentId]: { ...r[studentId], [type]: { ...r[studentId][type], [sem]: value } },
    }));
  }

  function setCgpa(studentId, value) {
    setRows((r) => ({ ...r, [studentId]: { ...r[studentId], cgpa: value } }));
  }

  async function save() {
    const records = (batch?.students || []).map((st) => ({ student_id: st.id, ...rows[st.id] }));
    await semesterResults.save(batchId, records);
  }

  async function handleSave() {
    setSaving(true); setError(""); setSuccess("");
    try {
      await save();
      setSuccess("Results saved!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }

  async function downloadPdf() {
    if (!academicYear.trim()) { setError("Enter the academic year for the PDF heading"); return; }
    setPdfLoading(true); setError("");
    try {
      await save();   // the PDF is built from saved data
      await downloadFile(
        semesterResults.pdfUrl(batchId, academicYear.trim()),
        `gpa_cgpa_arrears_${batch?.batch_year}.pdf`,
      );
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(false); }
  }

  if (loading) return <PageSpinner />;

  const students = [...(batch?.students || [])].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current="GPA, CGPA & Arrears" title="Semester" accent="Results">
        <input className="form-input" style={{ width: 170 }} placeholder="Academic year"
          value={academicYear} onChange={(e) => setAcademicYear(e.target.value)} />
        <button className="btn btn-ghost" style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
          onClick={downloadPdf} disabled={pdfLoading || students.length === 0}>
          {pdfLoading ? <span className="spinner" /> : <><FileDown size={16} strokeWidth={1.8} /> PDF</>}
        </button>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving || students.length === 0}>
          {saving ? <span className="spinner" /> : "Save Results"}
        </button>
      </MentorFileHeader>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 20 }}>{success}</div>}

      <div style={{ display: "flex", gap: 10, marginBottom: 20 }}>
        {TABS.map(({ key, label, Icon, color }) => (
          <button key={key} className="btn btn-ghost btn-sm" onClick={() => setTab(key)}
            style={tab === key ? { color, borderColor: color, background: "var(--surface-muted)" } : {}}>
            <Icon size={15} strokeWidth={1.8} /> {label}
          </button>
        ))}
      </div>

      {students.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><Users size={40} strokeWidth={1.2} /></div>
          <h3>No students in this batch</h3>
          <p>Add students to the batch before entering results.</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: "hidden" }}>
          <div className="table-wrapper" style={{ border: "none", borderRadius: 0, overflowX: "auto" }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>S.NO</th>
                  <th>Register Number</th>
                  <th>Name of the Student</th>
                  {SEMESTER_KEYS.map((k) => <th key={k} style={{ textAlign: "center" }}>S{k}</th>)}
                  <th style={{ textAlign: "center" }}>CGPA</th>
                </tr>
              </thead>
              <tbody>
                {students.map((st, idx) => (
                  <tr key={st.id}>
                    <td style={{ color: "var(--text-muted)", textAlign: "center" }}>{idx + 1}</td>
                    <td><span className="badge badge-purple">{st.register_number}</span></td>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>{st.name}</td>
                    {SEMESTER_KEYS.map((k) => (
                      <td key={k} style={{ textAlign: "center" }}>
                        <input className="form-input" style={cellInput} inputMode="decimal"
                          value={rows[st.id]?.[tab]?.[k] || ""}
                          onChange={(e) => setValue(st.id, tab, k, e.target.value)} />
                      </td>
                    ))}
                    <td style={{ textAlign: "center" }}>
                      <input className="form-input" style={cellInput} inputMode="decimal"
                        value={rows[st.id]?.cgpa || ""} onChange={(e) => setCgpa(st.id, e.target.value)} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <p style={{ color: "var(--text-muted)", fontSize: "0.8rem", marginTop: 12 }}>
        {tab === "gpa"
          ? "Enter the GPA secured in each semester and the current CGPA."
          : "Enter the number of arrears in each semester. CGPA is shared with the GPA tab."}
      </p>
    </>
  );
}
