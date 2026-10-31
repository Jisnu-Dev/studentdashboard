"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { batches, mentorFile } from "@/lib/api";
import { downloadFile } from "@/lib/download";
import { PageSpinner } from "@/components/MentorFileParts";
import { FileDown, ChevronRight, CheckCircle, MinusCircle } from "@/lib/icons";

// The 11 items of the Mentor File check list, in order.
function checklist(batchId, s) {
  const base = `/dashboard/batches/${batchId}`;
  return [
    { title: "Student Name List", note: "Export PDF from the batch page",
      href: base, status: `${s.students} students`, done: s.students > 0 },
    { title: "Student Personal Details", note: "Upload the CAMPS student record for each student",
      href: `${base}/personal-details`,
      status: `${s.personal_details} of ${s.students} students`, done: s.students > 0 && s.personal_details >= s.students },
    { title: "Student Counseling Form", note: "Minimum two sessions per student every semester — open a student's Counseling",
      href: base, status: `${s.counseling_sessions} sessions · ${s.students_counseled} of ${s.students} students`,
      done: s.students > 0 && s.students_counseled >= s.students },
    { title: "Mentor Mentee Meeting", note: "Weekly circular and minutes, plus the mentor note of communications",
      href: `${base}/meetings`, status: `${s.meetings} meetings`, done: s.meetings > 0,
      extra: { label: `Mentor Note (${s.communications})`, href: `${base}/communications` } },
    { title: "PT 1, PT 2 & SEE Subjectwise (Marks & Grade)", note: "Marks and grades for every semester",
      href: `${base}/exams`, status: `${s.exam_setups} semesters`, done: s.exam_setups > 0 },
    { title: "PT 1, PT 2 & SEE Results & Analysis", note: "Open an exam record › Analysis; record remedial actions there",
      href: `${base}/exams`, status: `${s.remedial_actions} remedial actions`, done: s.exam_setups > 0 },
    { title: "Parental Communication Report", note: "Parent - Teachers Meeting form",
      href: `${base}/parent-meetings`, status: `${s.parent_meetings} reports`, done: s.parent_meetings > 0 },
    { title: "Medical Leave Report / Proof", note: "If applicable — medical certificate or parent letter",
      href: `${base}/medical-leave`, status: `${s.medical_leaves} records`, done: s.medical_leaves > 0, optional: true },
    { title: "Student Achievements", note: "Certificates and the achievements summary sheet",
      href: `${base}/achievements`, status: `${s.achievements} achievements`, done: s.achievements > 0 },
    { title: "Condonation Form Submitted Student Details", note: "If applicable — approved form with medical certificate",
      href: `${base}/condonations`, status: `${s.condonations} applications`, done: s.condonations > 0, optional: true },
    { title: "Semesterwise GPA, CGPA and Arrear Details", note: "Semester End Examination results",
      href: `${base}/results`, status: `${s.semester_results} of ${s.students} students`,
      done: s.students > 0 && s.semester_results >= s.students },
  ];
}

export default function MentorFilePage() {
  const { id: batchId } = useParams();

  const [batch, setBatch] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    Promise.all([batches.get(batchId), mentorFile.summary(batchId)])
      .then(([b, s]) => { setBatch(b); setSummary(s); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [batchId]);

  async function downloadCover() {
    setPdfLoading(true); setError("");
    try {
      await downloadFile(mentorFile.coverUrl(batchId), `mentor_file_cover_${batch.batch_year}.pdf`);
    } catch (e) { setError(e.message); }
    finally { setPdfLoading(false); }
  }

  if (loading) return <PageSpinner />;

  const items = summary ? checklist(batchId, summary) : [];

  return (
    <>
      <div className="page-header">
        <div>
          <div className="breadcrumb">
            <Link href="/dashboard"><span>Dashboard</span></Link>
            <span className="sep">›</span>
            <Link href={`/dashboard/batches/${batchId}`}><span>{batch?.batch_year}</span></Link>
            <span className="sep">›</span>
            <span className="current">Mentor File</span>
          </div>
          <h1>Mentor <span className="gradient-text">File</span></h1>
          {batch && <p style={{ color: "var(--text-secondary)", marginTop: 4 }}>Department of {batch.department}</p>}
        </div>
        <button className="btn btn-primary" onClick={downloadCover} disabled={pdfLoading || !batch}>
          {pdfLoading ? <span className="spinner" /> : <><FileDown size={16} strokeWidth={1.8} /> Cover Page</>}
        </button>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 20 }}>{error}</div>}

      <div className="stats-row">
        <div className="card stat-card">
          <div className="stat-value">{items.filter((i) => i.done).length} / {items.length}</div>
          <div className="stat-label">Check List Items Started</div>
        </div>
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {items.map((item, idx) => (
          <div key={item.title} className="card" style={{ padding: "18px 24px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
              <span style={{ color: item.done ? "var(--success)" : "var(--text-muted)", flexShrink: 0 }}>
                {item.done ? <CheckCircle size={22} strokeWidth={1.8} /> : <MinusCircle size={22} strokeWidth={1.8} />}
              </span>
              <div style={{ flex: 1, minWidth: 240 }}>
                <div style={{ fontWeight: 700, color: "var(--text-primary)" }}>
                  {idx + 1}. {item.title}
                  {item.optional && <span style={{ fontWeight: 400, color: "var(--text-muted)", fontSize: "0.8rem" }}> (if applicable)</span>}
                </div>
                <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: 2 }}>{item.note}</div>
              </div>
              <span className="badge badge-purple">{item.status}</span>
              {item.extra && (
                <Link href={item.extra.href} className="btn btn-ghost btn-sm">{item.extra.label}</Link>
              )}
              <Link href={item.href} className="btn btn-ghost btn-sm"
                style={{ color: "var(--accent)", borderColor: "var(--accent-border)" }}>
                Open <ChevronRight size={14} strokeWidth={1.8} />
              </Link>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}
