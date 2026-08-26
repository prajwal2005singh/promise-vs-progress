import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { SubmitButton, ErrorText } from "../components/AuthCard";
import { formatDateTime } from "../lib/format";

export default function UploadEvidence() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [projectId, setProjectId] = useState("");
  const [description, setDescription] = useState("");
  const [photo, setPhoto] = useState(null);
  const [photoPreview, setPhotoPreview] = useState(null);
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    api.listProjects().then((ps) => {
      setProjects(ps);
      if (ps.length) setProjectId(ps[0].id);
    }).catch(() => {});
  }, []);

  function onPickPhoto(e) {
    const file = e.target.files?.[0] || null;
    setPhoto(file);
    setPhotoPreview(file ? URL.createObjectURL(file) : null);
  }

  async function onSubmit(e) {
    e.preventDefault();
    setError(null);

    if (!photo) {
      setError("Attach a photo taken with your camera -- location must be on when it's taken.");
      return;
    }

    setBusy(true);
    try {
      const res = await api.uploadEvidencePhoto(parseInt(projectId, 10), description, photo);
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  function submitAnother() {
    setResult(null);
    setPhoto(null);
    setPhotoPreview(null);
    setDescription("");
    if (fileInputRef.current) fileInputRef.current.value = "";
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

  if (result) {
    const { evidence, construction_visible, likely_active_site, matching_report_ids, context } = result;
    return (
      <div className="max-w-xl mx-auto px-6 py-20 text-center">
        <p className="font-display text-2xl mb-2" style={{ color: "var(--color-ink)" }}>{evidence.status === "APPROVED" ? "Evidence verified" : "Submitted for review"}</p>
        <p className="mb-6" style={{ color: "var(--color-ink-soft)" }}>
          {evidence.status === "APPROVED" ? "Your photo passed the context checks and the Image Engine accepted it automatically. It is already anchored on-chain and can enter the public evidence history." : "Your photo passed the context checks but the Image Engine was not confident enough to make the final call. It remains in the administrator review queue."}
        </p>

        <div className="text-left p-5 rounded-lg border mb-4" style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}>
          <p className="font-mono text-xs uppercase tracking-widest mb-3" style={{ color: "var(--color-marigold-deep)" }}>
            What the system saw
          </p>
          <dl className="space-y-2 text-sm">
            <InfoRow label="Construction visible" value={construction_visible ? "Yes" : "Not clearly"} />
            {evidence.ai_stage && (
              <InfoRow label="Predicted stage" value={`${evidence.ai_stage}${evidence.ai_stage_completion ? ` · ${evidence.ai_stage_completion.toLowerCase()}` : ""}`} />
            )}
            {evidence.ai_broad_stage && (
              <InfoRow label="Broad class" value={evidence.ai_broad_stage} />
            )}
            {evidence.ai_objects?.length > 0 && (
              <InfoRow label="Objects noted" value={evidence.ai_objects.join(", ")} />
            )}
            <InfoRow label="Captured" value={formatDateTime(evidence.captured_at)} />
            {context && (
              <InfoRow label="Location check" value={`${context.overall_status} · ${context.distance_to_project_m} m from project point`} />
            )}
            <InfoRow
              label="Confirming citizens"
              value={`${evidence.confirming_citizens} ${evidence.confirming_citizens === 1 ? "citizen" : "citizens"}${matching_report_ids.length ? " (including prior reports of this same spot)" : ""}`}
            />
          </dl>
          {evidence.ai_reason && (
            <p className="text-xs mt-3 italic" style={{ color: "var(--color-ink-soft)" }}>"{evidence.ai_reason}"</p>
          )}
          {!likely_active_site && (
            <p className="text-xs mt-3" style={{ color: "var(--color-ink-soft)" }}>
              The Image Engine was uncertain, so an administrator will review this observation before it becomes public.
            </p>
          )}
        </div>

        <div className="flex gap-3 justify-center">
          <button onClick={submitAnother} className="text-sm font-medium underline" style={{ color: "var(--color-marigold-deep)" }}>
            Submit another report
          </button>
          <Link to="/projects" className="text-sm font-medium underline" style={{ color: "var(--color-marigold-deep)" }}>
            Back to the register
          </Link>
        </div>
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
        Photograph what you see with your camera, right where you're standing. Location and time
        are read straight from the photo, checked against past reports, and given a first AI
        read -- then hashed on-chain. High-confidence observations are accepted automatically; only uncertain observations go to an administrator.
      </p>

      <form onSubmit={onSubmit} className="p-6 rounded-lg border" style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}>
        <label className="block mb-4">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>Project</span>
          <select
            required
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
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
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Resurfacing complete on the Tumkur–Sira stretch, drainage still incomplete near km 12"
            className="w-full px-3 py-2.5 rounded border text-sm"
            style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
          />
        </label>

        <label className="block mb-2">
          <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>Photo</span>
          <input
            ref={fileInputRef}
            required
            type="file"
            accept="image/*"
            capture="environment"
            onChange={onPickPhoto}
            className="w-full text-sm"
            style={{ color: "var(--color-ink)" }}
          />
        </label>
        <p className="text-xs mb-4" style={{ color: "var(--color-ink-soft)" }}>
          Use the original camera file, not one forwarded over WhatsApp/Telegram -- those strip
          location data, and a photo without it will be rejected.
        </p>

        {photoPreview && (
          <img src={photoPreview} alt="Preview" className="w-full h-48 object-cover rounded border mb-4" style={{ borderColor: "var(--color-line)" }} />
        )}

        <SubmitButton disabled={busy || !projects.length}>{busy ? "Checking photo…" : "Submit report"}</SubmitButton>
        <ErrorText>{error}</ErrorText>
      </form>
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="flex items-start justify-between gap-4">
      <dt style={{ color: "var(--color-ink-soft)" }}>{label}</dt>
      <dd className="font-medium text-right" style={{ color: "var(--color-ink)" }}>{value}</dd>
    </div>
  );
}
