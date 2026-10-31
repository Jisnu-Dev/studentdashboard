import { TrendingUp, Sparkles, FileCheck, ShieldCheck } from "@/lib/icons";

const FEATURES = [
  { Icon: TrendingUp, title: "Early-warning risk levels", text: "Marks, arrears and attendance combined into a clear Low, Medium or High signal." },
  { Icon: Sparkles, title: "AI reports and study plans", text: "A written analysis and a weekly plan for each student, grounded in their records." },
  { Icon: FileCheck, title: "Mentor File, ready to print", text: "All eleven checklist items exported as PDFs in the institute format." },
];

/**
 * Split-screen layout shared by the sign-in and sign-up pages:
 * brand panel on the left, the form on the right.
 */
export default function AuthShell({ title, subtitle, children, footer }) {
  return (
    <div className="auth-shell">
      <aside className="auth-brand">
        <div className="auth-brand-top">
          <div className="auth-mark">M</div>
          <div>
            <div className="auth-brand-name">MentorBoard</div>
            <div className="auth-brand-sub">Bannari Amman Institute of Technology</div>
          </div>
        </div>

        <div className="auth-brand-body">
          <h2>Know every mentee.<br />Act before results arrive.</h2>
          <p className="auth-brand-lead">
            One place for counseling, meetings, marks and parent records, with the analysis done for you.
          </p>
          <ul className="auth-features">
            {FEATURES.map(({ Icon, title: t, text }) => (
              <li key={t}>
                <span className="auth-feature-icon"><Icon size={18} strokeWidth={1.8} /></span>
                <span>
                  <strong>{t}</strong>
                  <small>{text}</small>
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="auth-brand-foot">
          <ShieldCheck size={15} strokeWidth={1.8} />
          Each mentor sees only their own batches.
        </div>
      </aside>

      <main className="auth-main">
        <div className="auth-panel">
          <div className="auth-mobile-brand">
            <div className="auth-mark small">M</div>
            <span>MentorBoard</span>
          </div>
          <h1 className="auth-title">{title}</h1>
          <p className="auth-subtitle">{subtitle}</p>
          {children}
          <p className="auth-switch">{footer}</p>
        </div>
      </main>
    </div>
  );
}
