"use client";
import { useEffect, useState, useCallback, useMemo, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ai, batches, students } from "@/lib/api";
import { getToken } from "@/lib/auth";
import StudentModal from "@/components/StudentModal";
import ConfirmModal from "@/components/ConfirmModal";
import {
  Calendar, BarChart2, Pencil, Trash2, FileDown, Plus, ClipboardList, Bot, Users, FolderOpen,
  Search, ChevronRight, AlertCircle,
} from "@/lib/icons";

const LEVELS = ["High", "Medium", "Low"];

function initials(name) {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}

export default function BatchDetailPage() {
  const { id } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [studentModal, setStudentModal] = useState(null); // null | { mode: "add" } | { mode: "edit", student }
  const [confirmDelete, setConfirmDelete] = useState(null); // null | { type: "student"|"batch", id? }
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  const [editingBatch, setEditingBatch] = useState(false);
  const [batchForm, setBatchForm] = useState({ department: "", batch_year: "" });
  const [batchSaving, setBatchSaving] = useState(false);

  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState("All");
  const [insights, setInsights] = useState({}); // studentId -> { level, score, reasons, pt, cgpa }
  const asked = useRef(new Set());
  const hasBatch = useRef(false);

  const load = useCallback(async () => {
    try {
      const data = await batches.get(id);
      setBatch(data);
      hasBatch.current = true;
      setBatchForm({ department: data.department, batch_year: data.batch_year });
      try { sessionStorage.setItem(`batch:${id}`, JSON.stringify(data)); } catch { /* ignore */ }
    } catch (e) {
      // A failed background refresh is silent when the page already has data to show.
      if (!hasBatch.current) setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    // A revisit shows the saved copy straight away while the fresh one loads.
    try {
      const saved = sessionStorage.getItem(`batch:${id}`);
      if (saved) { setBatch(JSON.parse(saved)); hasBatch.current = true; setLoading(false); }
    } catch { /* storage unavailable */ }
    load();
  }, [load, id]);

  // Show the last known risk levels straight away (kept for this browser session), then refresh them.
  useEffect(() => {
    try {
      const saved = sessionStorage.getItem(`risk:${id}`);
      if (saved) setInsights(JSON.parse(saved));
    } catch { /* storage unavailable */ }
  }, [id]);

  // Risk level, latest test average and CGPA for each student, a few requests at a time.
  useEffect(() => {
    if (!batch) return;
    const todo = batch.students.filter((s) => !asked.current.has(s.id));
    todo.forEach((s) => asked.current.add(s.id));
    let next = 0;
    async function worker() {
      while (next < todo.length) {
        const s = todo[next++];
        try {
          const o = await ai.overview(id, s.id);
          const m = o.snapshot.metrics;
          setInsights((p) => {
            const next = {
              ...p,
              [s.id]: { level: o.snapshot.risk.level, score: o.snapshot.risk.score, reasons: o.snapshot.risk.reasons,
                        pt: m.pt_average_pct, cgpa: m.cgpa },
            };
            try { sessionStorage.setItem(`risk:${id}`, JSON.stringify(next)); } catch { /* ignore */ }
            return next;
          });
        } catch { /* leave the cells empty */ }
      }
    }
    Array.from({ length: Math.min(4, todo.length) }, worker);
  }, [batch, id]);

  // ── Student CRUD ─────────────────────────────────────────────────────────────
  async function handleStudentSave(data) {
    if (studentModal?.mode === "add") {
      await students.add(id, data.register_number, data.name);
    } else {
      await students.update(id, studentModal.student.id, data);
      asked.current.delete(studentModal.student.id);
    }
    await load();
    setStudentModal(null);
  }

  async function handleDeleteStudent(studentId) {
    setDeleteLoading(true);
    try {
      await students.delete(id, studentId);
      await load();
    } finally {
      setDeleteLoading(false);
      setConfirmDelete(null);
    }
  }

  // ── Batch CRUD ───────────────────────────────────────────────────────────────
  async function handleBatchSave() {
    setBatchSaving(true);
    try {
      await batches.update(id, batchForm);
      await load();
      setEditingBatch(false);
    } finally {
      setBatchSaving(false);
    }
  }

  async function handleDeleteBatch() {
    setDeleteLoading(true);
    try {
      await batches.delete(id);
      router.push("/dashboard");
    } finally {
      setDeleteLoading(false);
      setConfirmDelete(null);
    }
  }

  // ── PDF export ───────────────────────────────────────────────────────────────
  async function handleExportPdf() {
    setPdfLoading(true);
    try {
      const token = getToken();
      const res = await fetch(batches.exportPdf(id), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("PDF generation failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `student_list_${batch.department.replace(/ /g, "_")}_${batch.batch_year}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    } finally {
      setPdfLoading(false);
    }
  }

  const sortedStudents = useMemo(
    () => [...(batch?.students || [])].sort((a, b) => a.name.localeCompare(b.name)),
    [batch]
  );

  const counts = useMemo(() => {
    const c = { High: 0, Medium: 0, Low: 0 };
    sortedStudents.forEach((s) => { const l = insights[s.id]?.level; if (l) c[l]++; });
    return c;
  }, [sortedStudents, insights]);
  const assessed = counts.High + counts.Medium + counts.Low;
  const allAssessed = sortedStudents.length > 0 && assessed === sortedStudents.length;

  const visible = sortedStudents.filter((s) => {
    const q = query.trim().toLowerCase();
    const matchesQuery = !q || s.name.toLowerCase().includes(q) || s.register_number.toLowerCase().includes(q);
    const matchesFilter = filter === "All" || insights[s.id]?.level === filter;
    return matchesQuery && matchesFilter;
  });

  // ── Render ───────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "80px" }}>
        <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
      </div>
    );
  }

  if (error && !batch) {
    return <div className="alert alert-error" style={{ margin: 24 }}>{error}</div>;
  }

  if (!batch) return null;

  const base = `/dashboard/batches/${id}`;

  return (
    <>
      <div className="breadcrumb">
        <Link href="/dashboard"><span>Dashboard</span></Link>
        <span className="sep">›</span>
        <span className="current">{batch.batch_year}</span>
      </div>

      {/* Header */}
      <section className="card bh-head">
        <div className="bh-title">
          {!editingBatch ? (
            <>
              <span className="bh-eyebrow">Batch</span>
              <h1>{batch.batch_year}</h1>
              <p>Department of {batch.department}</p>
            </>
          ) : (
            <div className="bh-edit">
              <input className="form-input" value={batchForm.department} placeholder="Department"
                onChange={(e) => setBatchForm((f) => ({ ...f, department: e.target.value }))} />
              <input className="form-input" value={batchForm.batch_year} placeholder="Year (e.g. 2023-2027)"
                onChange={(e) => setBatchForm((f) => ({ ...f, batch_year: e.target.value }))} />
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={handleBatchSave} disabled={batchSaving}>
                  {batchSaving ? <span className="spinner" /> : "Save"}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => setEditingBatch(false)}>Cancel</button>
              </div>
            </div>
          )}
        </div>

        <div className="bh-actions">
          <button className="btn btn-primary" onClick={() => setStudentModal({ mode: "add" })}>
            <Plus size={16} strokeWidth={2} /> Add student
          </button>
          <button className="btn btn-ghost" onClick={handleExportPdf} disabled={pdfLoading}>
            {pdfLoading ? <span className="spinner" /> : <><FileDown size={15} strokeWidth={1.8} /> Export PDF</>}
          </button>
          <button className="btn btn-ghost icon-btn" title="Edit batch" aria-label="Edit batch"
            onClick={() => setEditingBatch(!editingBatch)}>
            <Pencil size={15} strokeWidth={1.8} />
          </button>
          <button className="btn btn-danger icon-btn" title="Delete batch" aria-label="Delete batch"
            onClick={() => setConfirmDelete({ type: "batch" })}>
            <Trash2 size={15} strokeWidth={1.8} />
          </button>
        </div>
      </section>

      {error && <div className="alert alert-error" style={{ marginBottom: 16 }}>{error}</div>}

      {/* Shortcuts */}
      <div className="bh-tiles">
        <Link href={`${base}/mentor-file`} className="card bh-tile">
          <span className="bh-tile-icon green"><FolderOpen size={20} strokeWidth={1.8} /></span>
          <span><strong>Mentor File</strong><small>11-item checklist and PDFs</small></span>
          <ChevronRight size={17} strokeWidth={1.8} className="bh-tile-arrow" />
        </Link>
        <Link href={`${base}/meetings`} className="card bh-tile">
          <span className="bh-tile-icon blue"><Calendar size={20} strokeWidth={1.8} /></span>
          <span><strong>Meetings</strong><small>Circulars, minutes, attendance</small></span>
          <ChevronRight size={17} strokeWidth={1.8} className="bh-tile-arrow" />
        </Link>
        <Link href={`${base}/exams`} className="card bh-tile">
          <span className="bh-tile-icon amber"><BarChart2 size={20} strokeWidth={1.8} /></span>
          <span><strong>Exams and analysis</strong><small>Marks, pass rates, remedial</small></span>
          <ChevronRight size={17} strokeWidth={1.8} className="bh-tile-arrow" />
        </Link>
      </div>

      {/* Risk summary */}
      <div className="bh-stats">
        <div className="card bh-stat">
          <div className="stat-value">{sortedStudents.length}</div>
          <div className="stat-label">Students</div>
        </div>
        {LEVELS.map((l) => (
          <button key={l} type="button" className={`card bh-stat risk-${l.toLowerCase()} ${filter === l ? "selected" : ""}`}
            onClick={() => setFilter(filter === l ? "All" : l)}>
            <div className="stat-value">{allAssessed ? counts[l] : "–"}</div>
            <div className="stat-label">{l} risk</div>
          </button>
        ))}
      </div>

      {/* Students */}
      <div className="card bh-students">
        <div className="bh-toolbar">
          <div>
            <h3>Students</h3>
            <span className="bh-sub">
              {allAssessed || sortedStudents.length === 0
                ? "Risk is calculated from marks, arrears, attendance and counseling records."
                : `Updating risk levels… ${assessed} of ${sortedStudents.length}`}
            </span>
          </div>
          <div className="bh-search">
            <Search size={15} strokeWidth={1.8} />
            <input placeholder="Search name or register number" value={query}
              onChange={(e) => setQuery(e.target.value)} />
          </div>
        </div>

        <div className="bh-filters">
          {["All", ...LEVELS].map((f) => (
            <button key={f} type="button" className={`chip ${filter === f ? "on" : ""}`} onClick={() => setFilter(f)}>
              {f === "All" ? `All (${sortedStudents.length})` : `${f} (${allAssessed ? counts[f] : "–"})`}
            </button>
          ))}
        </div>

        {sortedStudents.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon"><Users size={40} strokeWidth={1.2} /></div>
            <h3>No students yet</h3>
            <p style={{ marginBottom: 20 }}>Add students to this batch to get started.</p>
            <button className="btn btn-primary" onClick={() => setStudentModal({ mode: "add" })}>
              <Plus size={15} /> Add First Student
            </button>
          </div>
        ) : visible.length === 0 ? (
          <div className="empty-state"><p>No students match your search or filter.</p></div>
        ) : (
          <div className="table-wrapper" style={{ border: "none", borderRadius: 0 }}>
            <table className="bh-table">
              <thead>
                <tr>
                  <th style={{ width: 52 }}>S.NO</th>
                  <th>Student</th>
                  <th>Risk</th>
                  <th>Latest test</th>
                  <th>CGPA</th>
                  <th style={{ textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((student) => {
                  const ins = insights[student.id];
                  const n = sortedStudents.indexOf(student) + 1;
                  return (
                    <tr key={student.id}>
                      <td className="muted center">{n}</td>
                      <td>
                        <div className="bh-student">
                          <span className="bh-avatar">{initials(student.name)}</span>
                          <span>
                            <strong>{student.name}</strong>
                            <small>{student.register_number}</small>
                          </span>
                        </div>
                      </td>
                      <td>
                        {ins ? (
                          <span className={`risk-pill ${ins.level.toLowerCase()}`}
                            title={ins.reasons.join("\n")}>
                            <span className="dot" />{ins.level}
                          </span>
                        ) : <span className="skeleton" />}
                      </td>
                      <td className="num">{ins ? (ins.pt != null ? `${ins.pt}%` : "–") : <span className="skeleton short" />}</td>
                      <td className="num">{ins ? (ins.cgpa || "–") : <span className="skeleton short" />}</td>
                      <td>
                        <div className="bh-row-actions">
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => router.push(`${base}/students/${student.id}/counseling`)}>
                            <ClipboardList size={14} strokeWidth={1.8} /> Counseling
                          </button>
                          <button className="btn btn-ghost btn-sm bh-ai"
                            onClick={() => router.push(`${base}/students/${student.id}/ai`)}>
                            <Bot size={14} strokeWidth={1.8} /> AI
                          </button>
                          <button className="btn btn-ghost btn-sm icon-btn" title="Edit student" aria-label="Edit student"
                            onClick={() => setStudentModal({ mode: "edit", student })}>
                            <Pencil size={14} strokeWidth={1.8} />
                          </button>
                          <button className="btn btn-danger btn-sm icon-btn" title="Remove student" aria-label="Remove student"
                            onClick={() => setConfirmDelete({ type: "student", id: student.id })}>
                            <Trash2 size={14} strokeWidth={1.8} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {studentModal && (
        <StudentModal
          mode={studentModal.mode}
          initial={studentModal.student}
          onSave={handleStudentSave}
          onClose={() => setStudentModal(null)}
        />
      )}

      {confirmDelete && (
        <ConfirmModal
          title={confirmDelete.type === "batch" ? "Delete Batch?" : "Remove Student?"}
          message={
            confirmDelete.type === "batch"
              ? `This will permanently delete the batch "${batch.batch_year}" and all ${sortedStudents.length} students in it.`
              : "This will permanently remove the student from this batch."
          }
          danger
          loading={deleteLoading}
          onConfirm={() =>
            confirmDelete.type === "batch"
              ? handleDeleteBatch()
              : handleDeleteStudent(confirmDelete.id)
          }
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
