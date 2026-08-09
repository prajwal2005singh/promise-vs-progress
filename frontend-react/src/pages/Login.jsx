import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthCard, { Field, SubmitButton, ErrorText } from "../components/AuthCard";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await login(form.email, form.password);
      navigate("/projects");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Log in" subtitle="Access your citizen account to submit evidence or proposals.">
      <form onSubmit={onSubmit}>
        <Field
          label="Email"
          type="email"
          required
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
        />
        <Field
          label="Password"
          type="password"
          required
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
        />
        <SubmitButton disabled={busy}>{busy ? "Signing in…" : "Log in"}</SubmitButton>
        <ErrorText>{error}</ErrorText>
      </form>
      <p className="text-sm mt-5 text-center" style={{ color: "var(--color-ink-soft)" }}>
        New here?{" "}
        <Link to="/register" className="font-medium" style={{ color: "var(--color-marigold-deep)" }}>
          Register an account
        </Link>
      </p>
    </AuthCard>
  );
}
