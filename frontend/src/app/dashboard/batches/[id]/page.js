"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { batches, students } from "@/lib/api";
import { getToken } from "@/lib/auth";
import StudentModal from "@/components/StudentModal";
import ConfirmModal from "@/components/ConfirmModal";
import { Calendar, BarChart2, Pencil, Trash2, FileDown, Plus, ClipboardList, Bot, Users, GraduationCap } from "@/lib/icons";

export default function BatchDetailPage() {
  const { id } = useParams();
  const router = useRouter();

  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Modal state
  const [studentModal, setStudentModal] = useState(null); // null | { mode: "add" } | { mode: "edit", student }
  const [confirmDelete, setConfirmDelete] = useState(null); // null | { type: "student"|"batch", id? }
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);

  // Edit batch inline
  const [editingBatch, setEditingBatch] = useState(false);
  const [batchForm, setBatchForm] = useState({ department: "", batch_year: "" });
  const [batchSaving, setBatchSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await batches.get(id);
      setBatch(data);
      setBatchForm({ department: data.department, batch_year: data.batch_year });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  // ── Student CRUD ─────────────────────────────────────────────────────────────
  async function handleStudentSave(data) {
    if (studentModal?.mode === "add") {
      await students.add(id, data.register_number, data.name);
    } else {
      await students.update(id, studentModal.student.id, data);
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

  // ── Render ───────────────────────────────────────────────────────────────────
  if (loading) {
    return (
      <div style={{ display: "flex", justifyContent: "center", padding: "80px" }}>
        <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-error" style={{ margin: 24 }}>{error}</div>
    );
  }

  if (!batch) return null;

  const sortedStudents = [...(batch.students || [])].sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  return (
    <>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <span className="current">{batch.batch_year}</span>
          </div>
          {!editingBatch ? (
            <>
              <h1 style={{ marginBottom: 4 }}>{batch.batch_year}</h1>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                Department of {batch.department}
              </p>
            </>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 8 }}>
              <input
                className="form-input"
                value={batchForm.department}
                onChange={(e) => setBatchForm((f) => ({ ...f, department: e.target.value }))}
                placeholder="Department"
                style={{ maxWidth: 360 }}
              />
              <input
                className="form-input"
                value={batchForm.batch_year}
                onChange={(e) => setBatchForm((f) => ({ ...f, batch_year: e.target.value }))}
                placeholder="Year (e.g. 2023-2027)"
                style={{ maxWidth: 200 }}
              />
              <div style={{ display: "flex", gap: 8 }}>
                <button className="btn btn-primary btn-sm" onClick={handleBatchSave} disabled={batchSaving}>
                  {batchSaving ? <span className="spinner" /> : "Save"}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => setEditingBatch(false)}>Cancel</button>
              </div>
            </div>
          )}
        </div>

        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          <button className="btn btn-ghost btn-sm" style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
            onClick={() => router.push(`/dashboard/batches/${id}/meetings`)}>
            <Calendar size={15} strokeWidth={1.8} /> Meetings
          </button>
          <button className="btn btn-ghost btn-sm" style={{ color: "#fbbf24", borderColor: "rgba(251,191,36,0.3)" }}
            onClick={() => router.push(`/dashboard/batches/${id}/exams`)}>
            <BarChart2 size={15} strokeWidth={1.8} /> Exams
          </button>
          <button className="btn btn-ghost btn-sm" onClick={() => setEditingBatch(!editingBatch)}>
            <Pencil size={14} strokeWidth={1.8} /> Edit Batch
          </button>
          <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete({ type: "batch" })}>
            <Trash2 size={14} strokeWidth={1.8} /> Delete
          </button>
          <button className="btn btn-ghost btn-sm" onClick={handleExportPdf} disabled={pdfLoading}
            style={{ borderColor: "rgba(124,58,237,0.4)", color: "#a78bfa" }}>
            {pdfLoading ? <span className="spinner" /> : <><FileDown size={15} strokeWidth={1.8} /> Export PDF</>}
          </button>
          <button className="btn btn-primary btn-sm" onClick={() => setStudentModal({ mode: "add" })}>
            <Plus size={15} strokeWidth={2} /> Add Student
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{sortedStudents.length}</div>
          <div className="stat-label">Students</div>
        </div>
        <div className="card stat-card">
          <div className="stat-value">{batch.batch_year}</div>
          <div className="stat-label">Batch Year</div>
        </div>
      </div>

      {/* Students Table */}
      <div className="card" style={{ padding: 0, overflow: "hidden" }}>
        <div style={{
          padding: "20px 24px",
          borderBottom: "1px solid var(--glass-border)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center"
        }}>
          <h3>Students</h3>
          <span className="badge badge-purple">{sortedStudents.length} total</span>
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
        ) : (
          <div className="table-wrapper" style={{ border: "none", borderRadius: 0 }}>
            <table>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>S.NO</th>
                  <th>Register Number</th>
                  <th>Name of the Student</th>
                  <th style={{ width: 100, textAlign: "right" }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sortedStudents.map((student, idx) => (
                  <tr key={student.id}>
                    <td style={{ color: "var(--text-muted)", textAlign: "center" }}>
                      {idx + 1}
                    </td>
                    <td>
                      <span className="badge badge-purple">{student.register_number}</span>
                    </td>
                    <td style={{ color: "var(--text-primary)", fontWeight: 500 }}>
                      {student.name}
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                        <button className="btn btn-ghost btn-sm"
                          style={{ color: "#a78bfa", borderColor: "rgba(124,58,237,0.3)" }}
                          onClick={() => router.push(`/dashboard/batches/${id}/students/${student.id}/counseling`)}>
                          <ClipboardList size={14} strokeWidth={1.8} /> Counseling
                        </button>
                        <button className="btn btn-ghost btn-sm"
                          style={{ color: "#6ee7b7", borderColor: "rgba(16,185,129,0.3)" }}
                          onClick={() => router.push(`/dashboard/batches/${id}/students/${student.id}/ai`)}>
                          <Bot size={14} strokeWidth={1.8} /> AI
                        </button>
                        <button className="btn btn-ghost btn-sm"
                          onClick={() => setStudentModal({ mode: "edit", student })}>
                          <Pencil size={14} strokeWidth={1.8} />
                        </button>
                        <button className="btn btn-danger btn-sm"
                          onClick={() => setConfirmDelete({ type: "student", id: student.id })}>
                          <Trash2 size={14} strokeWidth={1.8} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Student Add/Edit Modal */}
      {studentModal && (
        <StudentModal
          mode={studentModal.mode}
          initial={studentModal.student}
          onSave={handleStudentSave}
          onClose={() => setStudentModal(null)}
        />
      )}

      {/* Confirm Delete Modal */}
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
