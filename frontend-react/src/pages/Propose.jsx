import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { Field, SubmitButton, ErrorText } from "../components/AuthCard";

const CATEGORIES = ["Road", "Government School", "Tunnel", "Other"];

export default function Propose() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "Road",
    location_name: "",
    latitude: "",
    longitude: "",
    budget: "",
  });
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  function set(key) {
    return (e) => setForm({ ...form, [key]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.createProposal({
        ...form,
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        budget: form.budget ? parseInt(form.budget, 10) : null,
      });
      setDone(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (!user) {
    return (
      <div className="max-w-md mx-auto px-6 py-20 text-center">
        <p style={{ color: "var(--color-ink-soft)" }}>
          Log in as a citizen to propose a project for the register.
        </p>
        <Link to="/login" className="inline-block mt-4 font-medium" style={{ color: "var(--color-marigold-deep)" }}>
          Log in →
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="max-w-md mx-auto px-6 py-20 text-center">
        <p className="font-display text-2xl mb-2" style={{ color: "var(--color-ink)" }}>Proposal submitted</p>
        <p style={{ color: "var(--color-ink-soft)" }}>
          An administrator will review it. Approved proposals are added to the public register.
        </p>
        <Link to="/projects" className="inline-block mt-4 font-medium" style={{ color: "var(--color-marigold-deep)" }}>
          Back to the register →
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-xl mx-auto px-6 py-14">
      <p className="font-mono text-xs uppercase tracking-[0.25em] mb-2" style={{ color: "var(--color-marigold-deep)" }}>
        Citizen Proposal
      </p>
      <h1 className="font-display text-3xl mb-2" style={{ color: "var(--color-ink)" }}>Propose a project</h1>
      <p className="text-sm mb-8" style={{ color: "var(--color-ink-soft)" }}>
        Know a road or school that needs government attention? Submit it here — an admin
        reviews every proposal before it enters the public register.
      </p>

      <form onSubmit={onSubmit} className="p-6 rounded-lg border" style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}>
        <Field label="Project name" required value={form.name} onChange={set("name")} />
        <label className="block mb-4">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>Description</span>
          <textarea
            required
            rows={4}
            value={form.description}
            onChange={set("description")}
            className="w-full px-3 py-2.5 rounded border text-sm"
            style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
          />
        </label>
        <label className="block mb-4">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>Category</span>
          <select
            value={form.category}
            onChange={set("category")}
            className="w-full px-3 py-2.5 rounded border text-sm"
            style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
          >
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <Field label="Location name" required value={form.location_name} onChange={set("location_name")} />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Latitude" type="number" step="any" required value={form.latitude} onChange={set("latitude")} />
          <Field label="Longitude" type="number" step="any" required value={form.longitude} onChange={set("longitude")} />
        </div>
        <Field label="Estimated budget (₹, optional)" type="number" value={form.budget} onChange={set("budget")} />
        <SubmitButton disabled={busy}>{busy ? "Submitting…" : "Submit proposal"}</SubmitButton>
        <ErrorText>{error}</ErrorText>
      </form>
    </div>
  );
}
