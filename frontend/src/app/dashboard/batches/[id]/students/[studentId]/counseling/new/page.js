"use client";
import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { counseling, batches } from "@/lib/api";

const ATTENDANCE_OPTIONS = ["Punctual", "Occasionally Tardy", "Habitually late", "Other"];
const DISCIPLINE_OPTIONS = ["Good", "Unkept", "Other"];
const ATTITUDE_OPTIONS = ["Willing, Eager, Pleasant", "Other"];

function today() {
  return new Date().toISOString().split("T")[0];
}

function currentAcademicYear() {
  const now = new Date();
  const y = now.getFullYear();
  return now.getMonth() >= 5 ? `${y}-${y + 1}` : `${y - 1}-${y}`;
}

export default function NewCounselingPage() {
  const { id: batchId, studentId } = useParams();
  const router = useRouter();

  const [student, setStudent] = useState(null);
  const [batch, setBatch] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [form, setForm] = useState({
    counseling_date: today(),
    academic_year: currentAcademicYear(),
    reason_initiated_by: "Institute Initiated",
    reason_details: "",
    attendance_status: "Punctual",
    attendance_other: "",
    discipline_status: "Good",
    discipline_other: "",
    attitude_status: "Willing, Eager, Pleasant",
    attitude_other: "",
    difficulty_meeting_demands: false,
    difficulty_explanation: "",
    corrective_action_needed: false,
    corrective_action_explanation: "",
    next_session_needed: false,
    next_session_explanation: "",
  });

  useEffect(() => {
    batches.get(batchId).then((b) => {
      setBatch(b);
      const s = b.students?.find((s) => String(s.id) === String(studentId));
      setStudent(s || null);
    });
  }, [batchId, studentId]);

  const set = (k) => (v) => setForm((f) => ({ ...f, [k]: v }));
  const setE = (k) => (e) => set(k)(e.target.value);
  const setB = (k) => (v) => set(k)(v);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const payload = { ...form };
      // Clean up "other" fields if not selected
      if (payload.attendance_status !== "Other") payload.attendance_other = null;
      if (payload.discipline_status !== "Other") payload.discipline_other = null;
      if (payload.attitude_status !== "Other") payload.attitude_other = null;
      if (!payload.difficulty_meeting_demands) payload.difficulty_explanation = null;
      if (!payload.corrective_action_needed) payload.corrective_action_explanation = null;
      if (!payload.next_session_needed) payload.next_session_explanation = null;
      // Empty strings → null
      Object.keys(payload).forEach((k) => {
        if (payload[k] === "") payload[k] = null;
      });

      await counseling.create(batchId, studentId, payload);
      router.push(`/dashboard/batches/${batchId}/students/${studentId}/counseling`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
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
            <Link href={`/dashboard/batches/${batchId}/students/${studentId}/counseling`}>
              <span>{student?.name || "Student"}</span>
            </Link>
            <span className="sep">›</span>
            <span className="current">New Session</span>
          </div>
          <h1>New <span className="gradient-text">Counseling Session</span></h1>
          {student && (
            <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>
              {student.register_number} — {student.name}
            </p>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} style={{ maxWidth: 720 }}>
        {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

        {/* ── Meta ── */}
        <Section title="Session Details">
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
            <div className="form-group">
              <label className="form-label">Date</label>
              <input className="form-input" type="date" value={form.counseling_date}
                onChange={setE("counseling_date")} required />
            </div>
            <div className="form-group">
              <label className="form-label">Academic Year</label>
              <input className="form-input" type="text" placeholder="2024-2025"
                value={form.academic_year} onChange={setE("academic_year")} required />
            </div>
          </div>
        </Section>

        {/* ── Q1 ── */}
        <Section title="1. Reason for Counseling">
          <div className="form-group">
            <label className="form-label">Initiated by</label>
            <div style={{ display: "flex", gap: 16 }}>
              {["Student Initiated", "Institute Initiated"].map((opt) => (
                <label key={opt} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
                  <input type="radio" name="reason_initiated_by" value={opt}
                    checked={form.reason_initiated_by === opt}
                    onChange={setE("reason_initiated_by")}
                    style={{ accentColor: "var(--accent)" }} />
                  {opt}
                </label>
              ))}
            </div>
          </div>
          <div className="form-group">
            <label className="form-label">Identify the reason (if any)</label>
            <input className="form-input" type="text" placeholder="Optional"
              value={form.reason_details} onChange={setE("reason_details")} />
          </div>
        </Section>

        {/* ── Q2 ── */}
        <Section title="2. General Observations">
          <RadioGroup label="a. Attendance" options={ATTENDANCE_OPTIONS}
            value={form.attendance_status} onChange={set("attendance_status")}
            otherValue={form.attendance_other} onOtherChange={setE("attendance_other")} />

          <RadioGroup label="b. Discipline" options={DISCIPLINE_OPTIONS}
            value={form.discipline_status} onChange={set("discipline_status")}
            otherValue={form.discipline_other} onOtherChange={setE("discipline_other")} />

          <RadioGroup label="c. Attitude" options={ATTITUDE_OPTIONS}
            value={form.attitude_status} onChange={set("attitude_status")}
            otherValue={form.attitude_other} onOtherChange={setE("attitude_other")} />
        </Section>

        {/* ── Q3-5 ── */}
        <Section title="3–5. Further Assessment">
          <YesNoField
            label="3. Is the student experiencing difficulty meeting course demands?"
            value={form.difficulty_meeting_demands}
            onChange={setB("difficulty_meeting_demands")}
            explanation={form.difficulty_explanation}
            onExplanation={setE("difficulty_explanation")}
          />
          <YesNoField
            label="4. Is corrective action needed?"
            value={form.corrective_action_needed}
            onChange={setB("corrective_action_needed")}
            explanation={form.corrective_action_explanation}
            onExplanation={setE("corrective_action_explanation")}
          />
          <YesNoField
            label="5. Next counseling session"
            value={form.next_session_needed}
            onChange={setB("next_session_needed")}
            explanation={form.next_session_explanation}
            onExplanation={setE("next_session_explanation")}
            yesLabel="Needed"
            noLabel="Not Needed"
          />
        </Section>

        {/* ── Actions ── */}
        <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
          <Link
            href={`/dashboard/batches/${batchId}/students/${studentId}/counseling`}
            className="btn btn-ghost"
            style={{ flex: 1, justifyContent: "center" }}
          >
            Cancel
          </Link>
          <button
            type="submit"
            className="btn btn-primary"
            style={{ flex: 3, justifyContent: "center" }}
            disabled={loading}
          >
            {loading ? <span className="spinner" /> : "Save Counseling Session"}
          </button>
        </div>
      </form>
    </>
  );
}

// ── Sub-components ─────────────────────────────────────────────────────────────

function Section({ title, children }) {
  return (
    <div className="card" style={{ padding: 24, marginBottom: 20 }}>
      <h3 style={{ marginBottom: 20, fontSize: "1rem", color: "var(--text-primary)" }}>
        {title}
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        {children}
      </div>
    </div>
  );
}

function RadioGroup({ label, options, value, onChange, otherValue, onOtherChange }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, paddingLeft: 4 }}>
        {options.map((opt) => (
          <div key={opt}>
            <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", color: "var(--text-secondary)", fontSize: "0.9rem" }}>
              <input type="radio" name={label} value={opt} checked={value === opt}
                onChange={() => onChange(opt)} style={{ accentColor: "var(--accent)" }} />
              {opt}
            </label>
            {opt === "Other" && value === "Other" && (
              <input
                className="form-input"
                style={{ marginTop: 8, marginLeft: 24 }}
                type="text"
                placeholder="Please specify..."
                value={otherValue}
                onChange={onOtherChange}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function YesNoField({ label, value, onChange, explanation, onExplanation, yesLabel = "Yes", noLabel = "No" }) {
  return (
    <div style={{ borderBottom: "1px solid var(--glass-border)", paddingBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
        <span style={{ fontSize: "0.875rem", color: "var(--text-secondary)", flex: 1 }}>{label}</span>
        <div style={{ display: "flex", gap: 16 }}>
          {[{ v: true, l: yesLabel }, { v: false, l: noLabel }].map(({ v, l }) => (
            <label key={l} style={{ display: "flex", alignItems: "center", gap: 6, cursor: "pointer", color: value === v ? "var(--accent)" : "var(--text-secondary)", fontSize: "0.875rem", fontWeight: value === v ? 600 : 400 }}>
              <input type="radio" name={label} checked={value === v}
                onChange={() => onChange(v)} style={{ accentColor: "var(--accent)" }} />
              {l}
            </label>
          ))}
        </div>
      </div>
      {value && (
        <div style={{ marginTop: 10, paddingLeft: 0 }}>
          <input className="form-input" type="text" placeholder="Explanation if any..."
            value={explanation} onChange={onExplanation}
            style={{ fontSize: "0.85rem" }} />
        </div>
      )}
    </div>
  );
}
