"use client";
import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { batches, parentMeetings } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import ConfirmModal from "@/components/ConfirmModal";
import { Field, MentorFileHeader, PageSpinner, StudentSelect, StudentTag, formGrid } from "@/components/MentorFileParts";
import { FileDown, Plus, Trash2, Users, X } from "@/lib/icons";

const RELATIONSHIPS = ["Father", "Mother", "Guardian"];
const ACTION_PLANS = ["Remedial Classes", "Mentorship", "Counseling", "Extra Assignments", "Others"];

// Q9 – Q11 of the form
const QUESTIONS = [
  ["periodic_reports", "9. Do you get periodic reports from the college with respect to your ward?"],
  ["interacts_regularly", "10. Do you interact with the college authorities regularly?"],
  ["satisfied_with_progress", "11. Are you satisfied with the progress of your ward (son/daughter)?"],
];

// Q12 – Q18 of the form
const DISCUSSION_POINTS = [
  ["academic_performance", "12. Academic Performance (marks in recent exams, strengths, areas of improvement)"],
  ["co_curricular", "13. Co-curricular & Extra-curricular Activities (sports, clubs, projects, etc.)"],
  ["attendance", "14. Attendance"],
  ["discipline", "15. Discipline"],
  ["placements", "16. Placements / Career Guidance"],
  ["concerns", "17. Any Specific Concerns / Feedback / Suggestions for the Department / College from Parent"],
  ["other_remarks", "18. Any other remarks"],
];

const today = () => new Date().toISOString().slice(0, 10);
const emptyForm = () => ({
  student_id: "", academic_year: "", meeting_date: today(),
  student_contact: "", semester_year_branch: "", parent_name: "", relationship_with_student: "Father",
  parent_contact: "", parent_address: "",
  periodic_reports: "", interacts_regularly: "", satisfied_with_progress: "",
  academic_performance: "", co_curricular: "", attendance: "", discipline: "", placements: "",
  concerns: "", other_remarks: "",
  action_plan: [], action_other: "", action_details: "",
});

export default function ParentMeetingsPage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [saving, setSaving] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);

  const load = useCallback(async () => {
    try {
      const [b, list] = await Promise.all([batches.get(batchId), parentMeetings.list(batchId)]);
      setBatch(b);
      setMeetings(list);
    } catch (e) { setError(e.message); }
    finally { setLoading(false); }
  }, [batchId]);

  useEffect(() => { load(); }, [load]);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  function togglePlan(option) {
    setForm((f) => ({
      ...f,
      action_plan: f.action_plan.includes(option)
        ? f.action_plan.filter((o) => o !== option)
        : [...f.action_plan, option],
    }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true); setError("");
    try {
      // Empty optional answers go as null
      const payload = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, v === "" ? null : v]));
      await parentMeetings.create(batchId, { ...payload, student_id: Number(form.student_id) });
      setForm(emptyForm());
      setShowForm(false);
      await load();
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  }

  async function downloadPdf(m) {
    setPdfLoading(m.id); setError("");
    try {
      await downloadFile(parentMeetings.pdfUrl(batchId, m.id), `parent_meeting_${m.register_number}_${m.meeting_date}.pdf`);
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(null); }
  }

  async function handleDelete(id) {
    setDeleteLoading(true);
    try { await parentMeetings.delete(batchId, id); await load(); }
    catch (e) { setError(e.message); }
    finally { setDeleteLoading(false); setConfirmDelete(null); }
  }

  if (loading) return <PageSpinner />;

  return (
    <>
      <MentorFileHeader batchId={batchId} batch={batch} current="Parental Communication" title="Parent - Teachers" accent="Meeting">
        <button className="btn btn-primary" onClick={() => setShowForm((v) => !v)}>
          {showForm ? <><X size={16} strokeWidth={2} /> Cancel</> : <><Plus size={16} strokeWidth={2} /> New Report</>}
        </button>
      </MentorFileHeader>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      {showForm && (
        <form className="card" style={{ padding: 24, marginBottom: 24 }} onSubmit={handleSubmit}>
          <h3 style={{ marginBottom: 18 }}>Parent - Teachers Meeting Form</h3>
          <div style={formGrid()}>
            <Field label="Student">
              <StudentSelect students={batch?.students || []} value={form.student_id}
                onChange={(v) => setForm((f) => ({ ...f, student_id: v }))} />
            </Field>
            <Field label="Academic Year">
              <input className="form-input" placeholder="e.g. 2025-2026" value={form.academic_year} onChange={set("academic_year")} required />
            </Field>
            <Field label="Date">
              <input className="form-input" type="date" value={form.meeting_date} onChange={set("meeting_date")} required />
            </Field>
            <Field label="3. Student Contact Number">
              <input className="form-input" value={form.student_contact} onChange={set("student_contact")} />
            </Field>
            <Field label="4. Semester / Year / Branch">
              <input className="form-input" placeholder="e.g. III / II / CSE" value={form.semester_year_branch} onChange={set("semester_year_branch")} />
            </Field>
            <Field label="5. Parent / Guardian Name">
              <input className="form-input" value={form.parent_name} onChange={set("parent_name")} required />
            </Field>
            <Field label="6. Relationship with Student">
              <select className="form-input" value={form.relationship_with_student} onChange={set("relationship_with_student")}>
                {RELATIONSHIPS.map((r) => <option key={r}>{r}</option>)}
              </select>
            </Field>
            <Field label="7. Contact Number">
              <input className="form-input" value={form.parent_contact} onChange={set("parent_contact")} />
            </Field>
            <Field label="8. Parent Contact Address">
              <input className="form-input" value={form.parent_address} onChange={set("parent_address")} />
            </Field>
          </div>

          <div style={{ ...formGrid(300), marginTop: 16 }}>
            {QUESTIONS.map(([key, label]) => (
              <Field key={key} label={label}>
                <input className="form-input" placeholder="Yes / No / remarks" value={form[key]} onChange={set(key)} />
              </Field>
            ))}
          </div>

          <h3 style={{ margin: "24px 0 14px" }}>Discussion Points</h3>
          <div style={formGrid(340)}>
            {DISCUSSION_POINTS.map(([key, label]) => (
              <Field key={key} label={label}>
                <textarea className="form-input" rows={2} value={form[key]} onChange={set(key)} />
              </Field>
            ))}
          </div>

          <h3 style={{ margin: "24px 0 14px" }}>Action Taken / Follow-up of the Meeting</h3>
          <div style={{ display: "flex", gap: 18, flexWrap: "wrap", marginBottom: 14 }}>
            {ACTION_PLANS.map((option) => (
              <label key={option} style={{ display: "flex", gap: 8, alignItems: "center", cursor: "pointer", color: "var(--text-primary)", fontSize: "0.9rem" }}>
                <input type="checkbox" checked={form.action_plan.includes(option)} onChange={() => togglePlan(option)} />
                {option}
              </label>
            ))}
          </div>
          <div style={formGrid(340)}>
            {form.action_plan.includes("Others") && (
              <Field label="Others (specify)">
                <input className="form-input" value={form.action_other} onChange={set("action_other")} />
              </Field>
            )}
            <Field label="Details of the action taken / follow-up">
              <textarea className="form-input" rows={3} value={form.action_details} onChange={set("action_details")} />
            </Field>
          </div>

          <button type="submit" className="btn btn-primary" style={{ marginTop: 18 }} disabled={saving}>
            {saving ? <span className="spinner" /> : "Save Report"}
          </button>
        </form>
      )}

      {meetings.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon"><Users size={40} strokeWidth={1.2} /></div>
          <h3>No parental communication reports yet</h3>
          <p>Record a parent meeting to file it in the mentor file.</p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {meetings.map((m) => (
            <div key={m.id} className="card" style={{ padding: 20 }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
                <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
                  <StudentTag record={m} />
                  <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                    {m.meeting_date} · AY {m.academic_year} · {m.parent_name} ({m.relationship_with_student})
                  </span>
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn btn-ghost btn-sm" style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}
                    onClick={() => downloadPdf(m)} disabled={pdfLoading === m.id}>
                    {pdfLoading === m.id ? <span className="spinner" /> : <><FileDown size={14} strokeWidth={1.8} /> PDF</>}
                  </button>
                  <button className="btn btn-danger btn-sm" onClick={() => setConfirmDelete(m.id)}>
                    <Trash2 size={14} strokeWidth={1.8} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {confirmDelete && (
        <ConfirmModal
          title="Delete Report?"
          message="This will permanently delete this parent meeting report."
          danger loading={deleteLoading}
          onConfirm={() => handleDelete(confirmDelete)}
          onClose={() => setConfirmDelete(null)}
        />
      )}
    </>
  );
}
