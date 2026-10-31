"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import AuthShell from "@/components/AuthShell";
import { AuthField, PasswordField, PasswordStrength } from "@/components/AuthFields";
import { User, Mail, Lock, ArrowRight, AlertCircle } from "@/lib/icons";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.register(form.name, form.email, form.password);
      // Auto-login after registration
      const data = await auth.login(form.email, form.password);
      saveToken(data.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Create your account"
      subtitle="Set up your mentor profile to start managing your batches."
      footer={<>Already have an account? <Link href="/login">Sign in</Link></>}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="alert alert-error auth-alert">
            <AlertCircle size={16} strokeWidth={1.8} /> {error}
          </div>
        )}

        <AuthField
          label="Full name"
          Icon={User}
          type="text"
          placeholder="Dr. A. Rajkumar"
          value={form.name}
          onChange={set("name")}
          autoComplete="name"
          required
          autoFocus
        />

        <AuthField
          label="Email address"
          Icon={Mail}
          type="email"
          placeholder="you@bitsathy.ac.in"
          value={form.email}
          onChange={set("email")}
          autoComplete="email"
          required
        />

        <PasswordField
          label="Password"
          Icon={Lock}
          placeholder="Create a password"
          value={form.password}
          onChange={set("password")}
          autoComplete="new-password"
          required
          minLength={8}
          hint={<PasswordStrength value={form.password} />}
        />

        <button className="btn btn-primary btn-lg auth-submit" type="submit" disabled={loading}>
          {loading ? <span className="spinner" /> : <>Create account <ArrowRight size={17} strokeWidth={2} /></>}
        </button>
      </form>
    </AuthShell>
  );
}
