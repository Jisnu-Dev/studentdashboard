"use client";
import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";
import { clearToken, isLoggedIn } from "@/lib/auth";
import { LayoutDashboard, Plus, LogOut, User } from "@/lib/icons";

export default function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [mentor, setMentor] = useState(null);

  useEffect(() => {
    if (!isLoggedIn()) { router.replace("/login"); return; }
    auth.me().then(setMentor).catch(() => { clearToken(); router.replace("/login"); });
  }, [router]);

  function logout() {
    clearToken();
    router.replace("/login");
  }

  const navItems = [
    { href: "/dashboard",            Icon: LayoutDashboard, label: "Dashboard" },
    { href: "/dashboard/batches/new", Icon: Plus,            label: "New Batch"  },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-text">MentorBoard</div>
        <div className="logo-sub">Bannari Amman Institute</div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ href, Icon, label }) => (
          <Link
            key={href}
            href={href}
            className={`nav-link ${pathname === href ? "active" : ""}`}
          >
            <Icon size={18} strokeWidth={1.8} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="sidebar-footer">
        {mentor && (
          <div className="mentor-chip">
            <div className="mentor-avatar">
              {mentor.name.charAt(0).toUpperCase()}
            </div>
            <div className="mentor-info">
              <div className="mentor-name">{mentor.name}</div>
              <div className="mentor-role">Mentor</div>
            </div>
          </div>
        )}
        <button
          className="btn btn-ghost"
          style={{ width: "100%", justifyContent: "center", gap: 8 }}
          onClick={logout}
        >
          <LogOut size={16} strokeWidth={1.8} />
          Sign Out
        </button>
      </div>
    </aside>
  );
}
