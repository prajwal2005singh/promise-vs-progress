import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { Field, SubmitButton, ErrorText } from "../components/AuthCard";

export default function UploadEvidence() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [form, setForm] = useState({
    project_id: "",
    description: "",
    image_url: "",
    latitude: "",
    longitude: "",
    captured_at: "",
  });
  const [error, setError] = useState(null);
  const [done, setDone] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.listProjects().then((ps) => {
      setProjects(ps);
      if (ps.length) setForm((f) => ({ ...f, project_id: ps[0].id }));
    }).catch(() => {});
  }, []);

  function set(key) {
    return (e) => setForm({ ...form, [key]: e.target.value });
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.uploadEvidence({
        ...form,
        project_id: parseInt(form.project_id, 10),
        latitude: parseFloat(form.latitude),
        longitude: parseFloat(form.longitude),
        captured_at: new Date(form.captured_at).toISOString(),
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
        <p style={{ color: "var(--color-ink-soft)" }}>Log in to submit a progress report.</p>
        <Link to="/login" className="inline-block mt-4 font-medium" style={{ color: "var(--color-marigold-deep)" }}>
          Log in →
        </Link>
      </div>
    );
  }

  if (done) {
    return (
      <div className="max-w-md mx-auto px-6 py-20 text-center">
        <p className="font-display text-2xl mb-2" style={{ color: "var(--color-ink)" }}>Submitted for review</p>
        <p style={{ color: "var(--color-ink-soft)" }}>
          Your report has already been hashed and anchored on-chain as raw evidence.
          Once an administrator verifies it, it'll appear publicly on the project page.
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
        Ground Truth
      </p>
      <h1 className="font-display text-3xl mb-2" style={{ color: "var(--color-ink)" }}>Submit a progress report</h1>
      <p className="text-sm mb-8" style={{ color: "var(--color-ink-soft)" }}>
        Photograph what you see, note where and when. It's hashed and anchored on-chain
        immediately, then reviewed by an administrator before appearing publicly.
      </p>

      <form onSubmit={onSubmit} className="p-6 rounded-lg border" style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}>
        <label className="block mb-4">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>Project</span>
          <select
            required
            value={form.project_id}
            onChange={set("project_id")}
            className="w-full px-3 py-2.5 rounded border text-sm"
            style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
          >
            {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </label>
        <label className="block mb-4">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>What did you see?</span>
          <textarea
            required
            rows={3}
            value={form.description}
            onChange={set("description")}
            placeholder="e.g. Resurfacing complete on the Tumkur–Sira stretch, drainage still incomplete near km 12"
            className="w-full px-3 py-2.5 rounded border text-sm"
            style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
          />
        </label>
        <Field label="Photo URL (optional)" type="url" value={form.image_url} onChange={set("image_url")} placeholder="https://…" />
        <div className="grid grid-cols-2 gap-3">
          <Field label="Latitude" type="number" step="any" required value={form.latitude} onChange={set("latitude")} />
          <Field label="Longitude" type="number" step="any" required value={form.longitude} onChange={set("longitude")} />
        </div>
        <Field label="When was this captured?" type="datetime-local" required value={form.captured_at} onChange={set("captured_at")} />
        <SubmitButton disabled={busy || !projects.length}>{busy ? "Submitting…" : "Submit report"}</SubmitButton>
        <ErrorText>{error}</ErrorText>
      </form>
    </div>
  );
}
