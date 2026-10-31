"use client";
import { useState } from "react";
import { Eye, EyeOff } from "@/lib/icons";

/** A labelled input with a leading icon. */
export function AuthField({ label, Icon, hint, ...input }) {
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div className="input-icon">
        <Icon size={17} strokeWidth={1.8} className="input-icon-left" />
        <input className="form-input" {...input} />
      </div>
      {hint}
    </div>
  );
}

/** Password input with a show/hide button. */
export function PasswordField({ label, Icon, hint, ...input }) {
  const [shown, setShown] = useState(false);
  return (
    <div className="form-group">
      <label className="form-label">{label}</label>
      <div className="input-icon">
        <Icon size={17} strokeWidth={1.8} className="input-icon-left" />
        <input className="form-input has-toggle" type={shown ? "text" : "password"} {...input} />
        <button
          type="button"
          className="input-toggle"
          onClick={() => setShown((v) => !v)}
          aria-label={shown ? "Hide password" : "Show password"}
        >
          {shown ? <EyeOff size={17} strokeWidth={1.8} /> : <Eye size={17} strokeWidth={1.8} />}
        </button>
      </div>
      {hint}
    </div>
  );
}

/** Four-bar strength meter for the sign-up password. */
export function PasswordStrength({ value }) {
  const score =
    (value.length >= 8 ? 1 : 0) +
    (/[A-Z]/.test(value) && /[a-z]/.test(value) ? 1 : 0) +
    (/\d/.test(value) ? 1 : 0) +
    (/[^A-Za-z0-9]/.test(value) ? 1 : 0);
  const labels = ["Use at least 8 characters", "Weak", "Fair", "Good", "Strong"];
  return (
    <div className="strength">
      <div className="strength-bars">
        {[1, 2, 3, 4].map((n) => (
          <span key={n} className={n <= score && value ? `on s${score}` : ""} />
        ))}
      </div>
      <span className="strength-label">{value ? labels[score] : labels[0]}</span>
    </div>
  );
}
