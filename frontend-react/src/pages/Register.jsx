import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import AuthCard, { Field, SubmitButton, ErrorText } from "../components/AuthCard";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", phone: "", password: "" });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  function set(key) {
    return (e) => setForm({ ...form, [key]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await register(form);
      navigate("/projects");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <AuthCard title="Register" subtitle="Create a citizen account to submit evidence or propose projects.">
      <form onSubmit={onSubmit}>
        <Field label="Full name" required value={form.name} onChange={set("name")} />
        <Field label="Email" type="email" required value={form.email} onChange={set("email")} />
        <Field label="Phone" type="tel" required value={form.phone} onChange={set("phone")} />
        <Field label="Password" type="password" required minLength={6} value={form.password} onChange={set("password")} />
        <SubmitButton disabled={busy}>{busy ? "Creating account…" : "Register"}</SubmitButton>
        <ErrorText>{error}</ErrorText>
      </form>
      <p className="text-sm mt-5 text-center" style={{ color: "var(--color-ink-soft)" }}>
        Already registered?{" "}
        <Link to="/login" className="font-medium" style={{ color: "var(--color-marigold-deep)" }}>
          Log in
        </Link>
      </p>
    </AuthCard>
  );
}
