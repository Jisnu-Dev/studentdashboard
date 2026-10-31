"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { auth } from "@/lib/api";
import { saveToken } from "@/lib/auth";
import AuthShell from "@/components/AuthShell";
import { AuthField, PasswordField } from "@/components/AuthFields";
import { Mail, Lock, ArrowRight, AlertCircle } from "@/lib/icons";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await auth.login(email, password);
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
      title="Welcome back"
      subtitle="Sign in to continue to your mentor dashboard."
      footer={<>New to MentorBoard? <Link href="/register">Create an account</Link></>}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && (
          <div className="alert alert-error auth-alert">
            <AlertCircle size={16} strokeWidth={1.8} /> {error}
          </div>
        )}

        <AuthField
          label="Email address"
          Icon={Mail}
          type="email"
          placeholder="you@bitsathy.ac.in"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
          required
          autoFocus
        />

        <PasswordField
          label="Password"
          Icon={Lock}
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />

        <button className="btn btn-primary btn-lg auth-submit" type="submit" disabled={loading}>
          {loading ? <span className="spinner" /> : <>Sign in <ArrowRight size={17} strokeWidth={2} /></>}
        </button>
      </form>
    </AuthShell>
  );
}
