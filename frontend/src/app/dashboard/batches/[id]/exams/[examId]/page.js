"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { exams, batches, students as studentsApi } from "@/lib/api";
import { getToken } from "@/lib/auth";
import { FileDown, BookOpen, GraduationCap, Pencil, Plus, X, RotateCcw } from "@/lib/icons";

const SEMESTERS = [
  "I Year - Semester I", "I Year - Semester II",
  "II Year - Semester III", "II Year - Semester IV",
  "III Year - Semester V", "III Year - Semester VI",
  "IV Year - Semester VII", "IV Year - Semester VIII",
];

const GRADES = ["", "O", "A+", "A", "B+", "B", "C", "U", "W", "AB"];

const TABS = [
  { key: "pt1",      label: "PT1 Marks",       Icon: BookOpen,      color: "#fbbf24", mark_key: "pt1" },
  { key: "pt2",      label: "PT2 Marks",       Icon: BookOpen,      color: "#a78bfa", mark_key: "pt2" },
  { key: "semester", label: "Semester Grades", Icon: GraduationCap, color: "#6ee7b7", mark_key: "sem" },
];

export default function ExamMarksPage() {
  const { id: batchId, examId } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [setup, setSetup] = useState(null);
  const [studentList, setStudentList] = useState([]);
  const [marks, setMarks] = useState({});  // {studentId: {pt1: {code:val}, pt2: {code:val}, sem: {code:val}}}
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [tab, setTab] = useState("pt1");
  const [editingSetup, setEditingSetup] = useState(false);
  const [setupForm, setSetupForm] = useState({ semester: "", academic_year: "", subject_codes: [] });

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [b, s, studs, savedMarks] = await Promise.all([
        batches.get(batchId),
        exams.get(batchId, examId),
        studentsApi.list(batchId),
        exams.getMarks(batchId, examId),
      ]);
      setBatch(b);
      setSetup(s);
      setSetupForm({ semester: s.semester, academic_year: s.academic_year, subject_codes: [...s.subject_codes] });
      setStudentList(studs);

      const map = {};
      studs.forEach(st => { map[st.id] = { pt1: {}, pt2: {}, sem: {} }; });
      savedMarks.forEach(rec => {
        if (map[rec.student_id]) {
          map[rec.student_id] = {
            pt1: rec.pt1_marks || {},
            pt2: rec.pt2_marks || {},
            sem: rec.semester_grades || {},
          };
        }
      });
      setMarks(map);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId, examId]);

  useEffect(() => { load(); }, [load]);

  function setMark(studentId, type, code, value) {
    setMarks(m => ({
      ...m,
      [studentId]: { ...m[studentId], [type]: { ...m[studentId][type], [code]: value } },
    }));
  }

  async function handleSave() {
    setSaving(true); setError(""); setSuccess("");
    try {
      const records = studentList.map(st => ({
        student_id: st.id,
        pt1_marks: marks[st.id]?.pt1 || {},
        pt2_marks: marks[st.id]?.pt2 || {},
        semester_grades: marks[st.id]?.sem || {},
      }));
      await exams.saveMarks(batchId, examId, records);
      setSuccess("Marks saved!");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  }

  async function handleSaveSetup() {
    try {
      const updated = await exams.update(batchId, examId, {
        ...setupForm,
        subject_codes: setupForm.subject_codes.filter(c => c.trim()),
      });
      setSetup(updated);
      setEditingSetup(false);
      await load();
    } catch (e) { setError(e.message); }
  }

  async function downloadPdf(type) {
    setPdfLoading(type); setError("");
    try {
      const token = getToken();
      const urlMap = {
        pt1: exams.pt1PdfUrl(batchId, examId),
        pt2: exams.pt2PdfUrl(batchId, examId),
        semester: exams.semesterPdfUrl(batchId, examId),
      };
      const fileMap = {
        pt1: "pt1_marks", pt2: "pt2_marks", semester: "semester_grades",
      };
      const res = await fetch(urlMap[type], { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) { const d = await res.json().catch(() => null); throw new Error(d?.detail || "PDF failed"); }
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${fileMap[type]}_${setup?.semester}_${batch?.batch_year}.pdf`.replace(/ /g, "_");
      a.click(); URL.revokeObjectURL(a.href);
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(null); }
  }

  if (loading) return (
    <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
    </div>
  );
  if (!setup) return null;

  const subjects = setup.subject_codes || [];
  const activeTab = TABS.find(t => t.key === tab);

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
            <span className="current">{setup.semester}</span>
          </div>
          <h1>Exam <span className="gradient-text">Marks</span></h1>
          <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
            {setup.semester} · {setup.academic_year} · {subjects.length} subjects
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#fbbf24", borderColor: "rgba(251,191,36,0.3)" }}
            onClick={() => downloadPdf("pt1")} disabled={pdfLoading === "pt1"}>
            {pdfLoading === "pt1" ? <span className="spinner" /> : <><FileDown size={15} strokeWidth={1.8} /> PT1</>}
          </button>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
            onClick={() => downloadPdf("pt2")} disabled={pdfLoading === "pt2"}>
            {pdfLoading === "pt2" ? <span className="spinner" /> : <><FileDown size={15} strokeWidth={1.8} /> PT2</>}
          </button>
          <button className="btn btn-ghost btn-sm"
            style={{ color: "#6ee7b7", borderColor: "rgba(16,185,129,0.3)" }}
            onClick={() => downloadPdf("semester")} disabled={pdfLoading === "semester"}>
            {pdfLoading === "semester" ? <span className="spinner" /> : <><FileDown size={15} strokeWidth={1.8} /> Semester</>}
          </button>
          <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save"}
          </button>
        </div>
      </div>

      {error   && <div className="alert alert-error"   style={{ marginBottom: 16 }}>{error}</div>}
      {success && <div className="alert alert-success" style={{ marginBottom: 16 }}>{success}</div>}

      {/* Setup info card */}
      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        {!editingSetup ? (
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 12 }}>
            <div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 8 }}>Subject Codes</div>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                {subjects.map(code => (
                  <span key={code} style={{
                    fontSize: "0.8rem", background: "rgba(124,58,237,0.15)",
                    color: "#c4b5fd", border: "1px solid rgba(124,58,237,0.3)",
                    padding: "3px 10px", borderRadius: 6, fontFamily: "monospace",
                  }}>{code}</span>
                ))}
              </div>
            </div>
            <button className="btn btn-ghost btn-sm" onClick={() => setEditingSetup(true)}><Pencil size={14} strokeWidth={1.8} /> Edit Setup</button>
          </div>
        ) : (
          <div>
            <h4 style={{ marginBottom: 12 }}>Edit Exam Setup</h4>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div className="form-group">
                <label className="form-label">Academic Year</label>
                <input className="form-input" value={setupForm.academic_year}
                  onChange={e => setSetupForm(f => ({ ...f, academic_year: e.target.value }))} />
              </div>
              <div className="form-group">
                <label className="form-label">Semester</label>
                <select className="form-input" value={setupForm.semester}
                  onChange={e => setSetupForm(f => ({ ...f, semester: e.target.value }))} style={{ cursor: "pointer" }}>
                  {SEMESTERS.map(s => <option key={s} value={s} style={{ background: "#13133a" }}>{s}</option>)}
                </select>
              </div>
            </div>
            <div className="form-group" style={{ marginBottom: 12 }}>
              <label className="form-label">Subject Codes</label>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(140px,1fr))", gap: 8 }}>
                {setupForm.subject_codes.map((code, idx) => (
                  <div key={idx} style={{ display: "flex", gap: 6 }}>
                    <input className="form-input" value={code}
                      onChange={e => { const a = [...setupForm.subject_codes]; a[idx] = e.target.value.toUpperCase(); setSetupForm(f => ({ ...f, subject_codes: a })); }}
                      style={{ fontFamily: "monospace" }} />
                    <button type="button" className="btn btn-danger btn-sm"
                      onClick={() => setSetupForm(f => ({ ...f, subject_codes: f.subject_codes.filter((_, i) => i !== idx) }))}><X size={12} strokeWidth={2.5} /></button>
                  </div>
                ))}
                <button type="button" className="btn btn-ghost btn-sm"
                onClick={() => setSetupForm(f => ({ ...f, subject_codes: [...f.subject_codes, ""] }))}><Plus size={14} /> Add</button>
              </div>
            </div>
            <div style={{ display: "flex", gap: 10 }}>
              <button className="btn btn-ghost btn-sm" onClick={() => setEditingSetup(false)}>Cancel</button>
              <button className="btn btn-primary btn-sm" onClick={handleSaveSetup}>Save Setup</button>
            </div>
          </div>
        )}
      </div>

      {/* Tab switcher */}
      <div style={{
        display: "flex", gap: 4, marginBottom: 20,
        background: "var(--glass-bg)", border: "1px solid var(--glass-border)",
        borderRadius: 10, padding: 4, width: "fit-content",
      }}>
        {TABS.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{
              padding: "8px 20px", borderRadius: 8, border: "none", cursor: "pointer",
              fontWeight: tab === t.key ? 700 : 500, fontSize: "0.85rem", transition: "all 0.2s",
              background: tab === t.key ? `linear-gradient(135deg, ${t.color}33, ${t.color}22)` : "transparent",
              color: tab === t.key ? t.color : "var(--text-secondary)",
              boxShadow: tab === t.key ? `0 0 0 1px ${t.color}55` : "none",
              display: "flex", alignItems: "center", gap: 6,
            }}>
            <t.Icon size={14} strokeWidth={1.8} />
            {t.label}
          </button>
        ))}
      </div>

      {/* Spreadsheet */}
      <div style={{ overflowX: "auto", borderRadius: 12, border: "1px solid var(--glass-border)" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 500 }}>
          <thead>
            <tr style={{ background: `${activeTab?.color}18` }}>
              <th style={TH}>S.No</th>
              <th style={TH}>Register No.</th>
              <th style={{ ...TH, textAlign: "left", minWidth: 160 }}>Student Name</th>
              {subjects.map(code => (
                <th key={code} style={{ ...TH, color: activeTab?.color }}>{code}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {studentList.map((student, idx) => {
              const rec = marks[student.id] || { pt1: {}, pt2: {}, sem: {} };
              const mk = rec[activeTab?.mark_key] || {};
              return (
                <tr key={student.id} style={{ background: idx % 2 === 0 ? "transparent" : "rgba(255,255,255,0.02)" }}>
                  <td style={TD}>{idx + 1}</td>
                  <td style={TD}>{student.register_number}</td>
                  <td style={{ ...TD, textAlign: "left", fontWeight: 500 }}>{student.name}</td>
                  {subjects.map(code => (
                    <td key={code} style={TD_INPUT}>
                      {tab === "semester" ? (
                        <select
                          value={mk[code] ?? ""}
                          onChange={e => setMark(student.id, "sem", code, e.target.value)}
                          style={{ ...INPUT_STYLE, cursor: "pointer", background: "#1a1a3e", color: activeTab?.color }}>
                          {GRADES.map(g => <option key={g} value={g} style={{ background: "#13133a" }}>{g || "—"}</option>)}
                        </select>
                      ) : (
                        <input
                          type="text" maxLength={3}
                          value={mk[code] ?? ""}
                          onChange={e => setMark(student.id, activeTab.mark_key, code, e.target.value)}
                          placeholder="—"
                          style={{ ...INPUT_STYLE, borderColor: `${activeTab?.color}44` }}
                        />
                      )}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Sticky save bar */}
      <div style={{
        position: "sticky", bottom: 20, marginTop: 20,
        background: "var(--glass-bg)", backdropFilter: "blur(16px)",
        border: "1px solid var(--glass-border)", borderRadius: 12,
        padding: "14px 20px", display: "flex", gap: 12,
        alignItems: "center", justifyContent: "space-between",
      }}>
        <span style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
          {studentList.length} students · {subjects.length} subjects · {activeTab?.label}
        </span>
        <button className="btn btn-primary" onClick={handleSave} disabled={saving}>
          {saving ? <span className="spinner" /> : "Save All Marks"}
        </button>
      </div>
    </>
  );
}

// ── Styles ─────────────────────────────────────────────────────────────────────

const TH = {
  padding: "10px 10px", fontSize: "0.75rem", fontWeight: 700, textAlign: "center",
  color: "var(--text-primary)", borderBottom: "1px solid var(--glass-border)",
  borderRight: "1px solid rgba(255,255,255,0.05)", whiteSpace: "nowrap",
};

const TD = {
  padding: "8px 10px", fontSize: "0.8rem", color: "var(--text-secondary)", textAlign: "center",
  borderBottom: "1px solid rgba(255,255,255,0.04)", borderRight: "1px solid rgba(255,255,255,0.04)",
};

const TD_INPUT = {
  padding: "4px 6px", borderBottom: "1px solid rgba(255,255,255,0.04)",
  borderRight: "1px solid rgba(255,255,255,0.04)",
};

const INPUT_STYLE = {
  width: "100%", minWidth: 60, textAlign: "center", background: "transparent",
  border: "1px solid rgba(124,58,237,0.25)", borderRadius: 6,
  color: "var(--text-primary)", fontSize: "0.8rem", padding: "5px 4px",
  outline: "none",
};
