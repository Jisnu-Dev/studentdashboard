"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { auth, batches } from "@/lib/api";
import { clearToken, isLoggedIn } from "@/lib/auth";
import {
  LayoutDashboard, Plus, LogOut, ArrowLeft, Users, FolderOpen, Calendar, BarChart2, TrendingUp,
  User, Phone, MessageSquare, Trophy, FileCheck, Stethoscope,
} from "@/lib/icons";

function NavItem({ href, Icon, label, active }) {
  return (
    <Link href={href} className={`nav-link ${active ? "active" : ""}`}>
      <Icon size={17} strokeWidth={1.8} />
      <span>{label}</span>
    </Link>
  );
}

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [mentor, setMentor] = useState(null);
  const [batch, setBatch] = useState(null);

  // /dashboard/batches/7/... -> "7"  (the "new" page is not a batch)
  const match = pathname.match(/^\/dashboard\/batches\/(\d+)/);
  const batchId = match ? match[1] : null;
  const base = batchId ? `/dashboard/batches/${batchId}` : null;

  useEffect(() => {
    if (!isLoggedIn()) { router.replace("/login"); return; }
    auth.me().then(setMentor).catch(() => { clearToken(); router.replace("/login"); });
  }, [router]);

  useEffect(() => {
    if (!batchId) { setBatch(null); return; }
    let cancelled = false;
    batches.get(batchId).then((b) => { if (!cancelled) setBatch(b); }).catch(() => {});
    return () => { cancelled = true; };
  }, [batchId]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  const on = (path) => pathname === path || pathname.startsWith(path + "/");

  const batchLinks = base && [
    { href: base, Icon: Users, label: "Students", active: pathname === base || pathname.includes("/students/") },
    { href: `${base}/mentor-file`, Icon: FolderOpen, label: "Mentor File", active: on(`${base}/mentor-file`) },
    { href: `${base}/meetings`, Icon: Calendar, label: "Meetings", active: on(`${base}/meetings`) },
    { href: `${base}/exams`, Icon: BarChart2, label: "Exams and analysis", active: on(`${base}/exams`) },
    { href: `${base}/results`, Icon: TrendingUp, label: "Semester results", active: on(`${base}/results`) },
  ];
  const recordLinks = base && [
    { href: `${base}/personal-details`, Icon: User, label: "Personal details", active: on(`${base}/personal-details`) },
    { href: `${base}/communications`, Icon: MessageSquare, label: "Mentor note", active: on(`${base}/communications`) },
    { href: `${base}/parent-meetings`, Icon: Phone, label: "Parent meetings", active: on(`${base}/parent-meetings`) },
    { href: `${base}/achievements`, Icon: Trophy, label: "Achievements", active: on(`${base}/achievements`) },
    { href: `${base}/condonations`, Icon: FileCheck, label: "Condonation", active: on(`${base}/condonations`) },
    { href: `${base}/medical-leave`, Icon: Stethoscope, label: "Medical leave", active: on(`${base}/medical-leave`) },
  ];

  return (
    <aside className="sidebar">
      <Link href="/dashboard" className="sidebar-brand">
        <span className="sidebar-mark">M</span>
        <span>
          <span className="logo-text">MentorBoard</span>
          <span className="logo-sub">Bannari Amman Institute</span>
        </span>
      </Link>

      <nav className="sidebar-nav">
        <div className="nav-group-label">Menu</div>
        <NavItem href="/dashboard" Icon={LayoutDashboard} label="Dashboard" active={pathname === "/dashboard"} />
        <NavItem href="/dashboard/batches/new" Icon={Plus} label="New batch" active={pathname === "/dashboard/batches/new"} />

        {base && (
          <>
            <div className="nav-group-label">Current batch</div>
            <div className="nav-batch">
              <div className="nav-batch-year">{batch ? batch.batch_year : <span className="skeleton" />}</div>
              <div className="nav-batch-dept">{batch ? batch.department : ""}</div>
            </div>
            {batchLinks.map((l) => <NavItem key={l.label} {...l} />)}

            <div className="nav-group-label">Mentor File records</div>
            {recordLinks.map((l) => <NavItem key={l.label} {...l} />)}

            <Link href="/dashboard" className="nav-back">
              <ArrowLeft size={15} strokeWidth={1.8} /> All batches
            </Link>
          </>
        )}
      </nav>

      <div className="sidebar-footer">
        {mentor && (
          <div className="mentor-chip">
            <div className="mentor-avatar">{mentor.name.charAt(0).toUpperCase()}</div>
            <div className="mentor-info">
              <div className="mentor-name">{mentor.name}</div>
              <div className="mentor-role">{mentor.email}</div>
            </div>
            <button className="sidebar-logout" onClick={logout} title="Sign out" aria-label="Sign out">
              <LogOut size={17} strokeWidth={1.8} />
            </button>
          </div>
        )}
      </div>
    </aside>
  );
}
