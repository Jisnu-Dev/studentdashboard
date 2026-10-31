"use client";
import Link from "next/link";

export const SEMESTERS = [
  "I Year - Semester I", "I Year - Semester II",
  "II Year - Semester III", "II Year - Semester IV",
  "III Year - Semester V", "III Year - Semester VI",
  "IV Year - Semester VII", "IV Year - Semester VIII",
];

export function PageSpinner() {
  return (
    <div style={{ display: "flex", justifyContent: "center", padding: 80 }}>
      <div className="spinner" style={{ width: 40, height: 40, borderWidth: 3 }} />
    </div>
  );
}

// Page header with the Dashboard › batch › Mentor File › current breadcrumb.
export function MentorFileHeader({ batchId, batch, current, title, accent, children }) {
  return (
    <div className="page-header">
      <div>
        <div className="breadcrumb">
          <Link href="/dashboard"><span>Dashboard</span></Link>
          <span className="sep">›</span>
          <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
          <span className="sep">›</span>
          <Link href={`/dashboard/batches/${batchId}/mentor-file`}><span>Mentor File</span></Link>
          <span className="sep">›</span>
          <span className="current">{current}</span>
        </div>
        <h1>{title} <span className="gradient-text">{accent}</span></h1>
        {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
      </div>
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>{children}</div>
    </div>
  );
}

export function Field({ label, children, style }) {
  return (
    <div className="form-group" style={style}>
      <label className="form-label">{label}</label>
      {children}
    </div>
  );
}

export function StudentSelect({ students, value, onChange, required = true }) {
  return (
    <select className="form-input" value={value} onChange={(e) => onChange(e.target.value)} required={required}>
      <option value="">Select student</option>
      {students.map((s) => (
        <option key={s.id} value={s.id}>{s.register_number} — {s.name}</option>
      ))}
    </select>
  );
}

export function StudentTag({ record }) {
  return (
    <>
      <span className="badge badge-purple">{record.register_number}</span>
      <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>{record.student_name}</span>
    </>
  );
}

export function formGrid(min = 220) {
  return { display: "grid", gridTemplateColumns: `repeat(auto-fit, minmax(${min}px, 1fr))`, gap: 16 };
}
