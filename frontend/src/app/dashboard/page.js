"use client";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth, batches, mentorFile } from "@/lib/api";
import {
  Plus, BookOpen, Users, GraduationCap, FolderOpen, Calendar, BarChart2, ChevronRight, Sparkles,
} from "@/lib/icons";

// How many of the 11 Mentor File checklist items have been started (same rules as the Mentor File page).
function itemsStarted(s) {
  const all = s.students > 0;
  return [
    s.students > 0,
    all && s.personal_details >= s.students,
    all && s.students_counseled >= s.students,
    s.meetings > 0,
    s.exam_setups > 0,
    s.exam_setups > 0,
    s.parent_meetings > 0,
    s.medical_leaves > 0,
    s.achievements > 0,
    s.condonations > 0,
    all && s.semester_results >= s.students,
  ].filter(Boolean).length;
}

function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}

export default function DashboardPage() {
  const router = useRouter();
  const [mentor, setMentor] = useState(null);
  const [batchList, setBatchList] = useState([]);
  const [details, setDetails] = useState({});   // batch id -> { students, started }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    auth.me().then(setMentor).catch(() => {});
    batches.list()
      .then((list) => {
        setBatchList(list);
        // The numbers on each card arrive one by one, so the page never waits for them.
        list.forEach((b) => {
          batches.get(b.id)
            .then((full) => setDetails((d) => ({ ...d, [b.id]: { ...d[b.id], students: full.students.length } })))
            .catch(() => {});
          mentorFile.summary(b.id)
            .then((s) => setDetails((d) => ({ ...d, [b.id]: { ...d[b.id], started: itemsStarted(s) } })))
            .catch(() => {});
        });
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const totalDepts = useMemo(() => new Set(batchList.map((b) => b.department)).size, [batchList]);
  const knownStudents = batchList.filter((b) => details[b.id]?.students !== undefined);
  const totalStudents = knownStudents.reduce((n, b) => n + details[b.id].students, 0);
  const studentsReady = batchList.length > 0 && knownStudents.length === batchList.length;

  const today = new Date().toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

  return (
    <>
      <section className="dash-hero">
        <div>
          <div className="dash-date"><Calendar size={14} strokeWidth={1.8} /> {today}</div>
          <h1>Welcome back, {mentor ? mentor.name : "…"}</h1>
          <p>
            {greeting()}.{" "}
            {batchList.length > 0
              ? "Pick a batch to continue with counseling, meetings, exams and your Mentor File."
              : "Create your first batch to start managing students."}
          </p>
        </div>
        <Link href="/dashboard/batches/new" className="btn dash-hero-btn">
          <Plus size={16} strokeWidth={2} /> New Batch
        </Link>
      </section>

      <div className="dash-stats">
        <div className="card dash-stat">
          <span className="dash-stat-icon blue"><FolderOpen size={20} strokeWidth={1.8} /></span>
          <div>
            <div className="stat-value">{loading ? "–" : batchList.length}</div>
            <div className="stat-label">Batches</div>
          </div>
        </div>
        <div className="card dash-stat">
          <span className="dash-stat-icon green"><Users size={20} strokeWidth={1.8} /></span>
          <div>
            <div className="stat-value">{studentsReady ? totalStudents : "–"}</div>
            <div className="stat-label">Students mentored</div>
          </div>
        </div>
        <div className="card dash-stat">
          <span className="dash-stat-icon amber"><GraduationCap size={20} strokeWidth={1.8} /></span>
          <div>
            <div className="stat-value">{loading ? "–" : totalDepts}</div>
            <div className="stat-label">Departments</div>
          </div>
        </div>
      </div>

      {error && <div className="alert alert-error" style={{ marginBottom: 24 }}>{error}</div>}

      <div className="dash-section-head">
        <h2>Your batches</h2>
        {batchList.length > 0 && <span className="dash-count">{batchList.length}</span>}
      </div>

      {loading && (
        <div style={{ display: "flex", justifyContent: "center", padding: "64px" }}>
          <div className="spinner" style={{ width: 36, height: 36, borderWidth: 3 }} />
        </div>
      )}

      {!loading && batchList.length === 0 && (
        <div className="card empty-state">
          <div className="empty-icon"><BookOpen size={40} strokeWidth={1.2} /></div>
          <h3>No batches yet</h3>
          <p style={{ marginBottom: 24 }}>Create your first batch to start managing students.</p>
          <Link href="/dashboard/batches/new" className="btn btn-primary">
            <Plus size={16} /> Create First Batch
          </Link>
        </div>
      )}

      {!loading && batchList.length > 0 && (
        <div className="batch-grid">
          {batchList.map((batch) => {
            const d = details[batch.id] || {};
            const pct = d.started !== undefined ? Math.round((d.started / 11) * 100) : 0;
            const base = `/dashboard/batches/${batch.id}`;
            return (
              <div key={batch.id} className="card batch-card dash-batch" onClick={() => router.push(base)}>
                <div className="dash-batch-top">
                  <div>
                    <div className="batch-card-dept">{batch.department}</div>
                    <div className="batch-card-year">{batch.batch_year}</div>
                  </div>
                  <span className="dash-batch-arrow"><ChevronRight size={18} strokeWidth={1.8} /></span>
                </div>

                <div className="dash-batch-students">
                  <Users size={15} strokeWidth={1.8} />
                  {d.students !== undefined ? `${d.students} students` : <span className="skeleton" />}
                </div>

                <div className="dash-progress">
                  <div className="dash-progress-label">
                    <span>Mentor File</span>
                    <span>{d.started !== undefined ? `${d.started} of 11 items started` : <span className="skeleton" />}</span>
                  </div>
                  <div className="dash-progress-bar"><span style={{ width: `${pct}%` }} /></div>
                </div>

                <div className="dash-batch-links" onClick={(e) => e.stopPropagation()}>
                  <Link href={`${base}/mentor-file`}><FolderOpen size={14} strokeWidth={1.8} /> Mentor File</Link>
                  <Link href={`${base}/meetings`}><Calendar size={14} strokeWidth={1.8} /> Meetings</Link>
                  <Link href={`${base}/exams`}><BarChart2 size={14} strokeWidth={1.8} /> Exams</Link>
                  <Link href={base}><Sparkles size={14} strokeWidth={1.8} /> Students and AI</Link>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
