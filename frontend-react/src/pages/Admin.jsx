import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { api } from "../lib/api";
import { formatBudget, formatDateTime } from "../lib/format";
import { Stamp } from "../components/Stamp";

export default function Admin() {
  const { user, loading } = useAuth();
  const [tab, setTab] = useState("proposals");

  if (loading) return null;

  if (!user || user.role !== "ADMIN") {
    return (
      <div className="max-w-md mx-auto px-6 py-20 text-center">
        <p style={{ color: "var(--color-ink-soft)" }}>The admin desk is restricted to administrators.</p>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <p className="font-mono text-xs uppercase tracking-[0.25em] mb-2" style={{ color: "var(--color-marigold-deep)" }}>
        Admin Desk
      </p>
      <h1 className="font-display text-3xl mb-8" style={{ color: "var(--color-ink)" }}>Review queue</h1>

      <div className="flex gap-6 mb-8 border-b" style={{ borderColor: "var(--color-line)" }}>
        <TabButton active={tab === "proposals"} onClick={() => setTab("proposals")}>Project proposals</TabButton>
        <TabButton active={tab === "evidence"} onClick={() => setTab("evidence")}>Evidence submissions</TabButton>
      </div>

      {tab === "proposals" ? <ProposalsTab /> : <EvidenceTab />}
    </div>
  );
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className="pb-3 text-sm font-medium -mb-px"
      style={{
        color: active ? "var(--color-ink)" : "var(--color-ink-soft)",
        borderBottom: active ? "2px solid var(--color-marigold-deep)" : "2px solid transparent",
      }}
    >
      {children}
    </button>
  );
}

function ProposalsTab() {
  const [proposals, setProposals] = useState(null);
  const [busyId, setBusyId] = useState(null);

      const reload = () =>
      api.listProposals()
        .then(setProposals)
        .catch(() => setProposals([]));

    useEffect(() => {
      reload();
    }, []);

  async function approve(id) {
    setBusyId(id);
    try {
      await api.approveProposal(id);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id) {
    const reason = prompt("Reason for rejecting this proposal?");
    if (!reason) return;
    setBusyId(id);
    try {
      await api.rejectProposal(id, reason);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  if (!proposals) return <p style={{ color: "var(--color-ink-soft)" }}>Loading…</p>;

  const pending = proposals.filter((p) => p.status === "PENDING");
  const reviewed = proposals.filter((p) => p.status !== "PENDING");

  return (
    <div>
      <Section title={`Needs human review (${pending.length})`}>
        {pending.length === 0 && <Empty>Nothing pending.</Empty>}
        {pending.map((p) => (
          <Card key={p.id}>
            <div className="flex-1">
              <p className="font-medium" style={{ color: "var(--color-ink)" }}>{p.name}</p>
              <p className="text-sm mt-0.5" style={{ color: "var(--color-ink-soft)" }}>{p.description}</p>
              <p className="text-xs font-mono mt-2" style={{ color: "var(--color-ink-soft)" }}>
                {p.category} · {p.location_name} · {formatBudget(p.budget)}
              </p>
            </div>
            <div className="flex gap-2 shrink-0">
              <ActionButton variant="green" onClick={() => approve(p.id)} disabled={busyId === p.id}>Approve</ActionButton>
              <ActionButton variant="red" onClick={() => reject(p.id)} disabled={busyId === p.id}>Reject</ActionButton>
            </div>
          </Card>
        ))}
      </Section>

      <Section title="Reviewed">
        {reviewed.map((p) => (
          <Card key={p.id}>
            <div className="flex-1">
              <p className="font-medium" style={{ color: "var(--color-ink)" }}>{p.name}</p>
              <p className="text-xs font-mono mt-1" style={{ color: "var(--color-ink-soft)" }}>{formatDateTime(p.updated_at)}</p>
            </div>
            <Stamp status={p.status} size="sm" />
          </Card>
        ))}
      </Section>
    </div>
  );
}

function EvidenceTab() {
  const [evidence, setEvidence] = useState(null);
  const [busyId, setBusyId] = useState(null);

  const reload = () =>
  api.listEvidence()
    .then(setEvidence)
    .catch(() => setEvidence([]));

useEffect(() => {
  reload();
}, []);

  async function approve(id) {
    setBusyId(id);
    try {
      await api.approveEvidence(id);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  async function reject(id) {
    const reason = prompt("Reason for rejecting this evidence?");
    if (!reason) return;
    setBusyId(id);
    try {
      await api.rejectEvidence(id, reason);
      reload();
    } finally {
      setBusyId(null);
    }
  }

  if (!evidence) return <p style={{ color: "var(--color-ink-soft)" }}>Loading…</p>;

  const pending = evidence.filter((e) => e.status === "PENDING");
  const reviewed = evidence.filter((e) => e.status !== "PENDING");

  return (
    <div>
      <Section title={`Needs human review (${pending.length})`}>
        {pending.length === 0 && <Empty>Nothing pending.</Empty>}
        {pending.map((e) => (
          <Card key={e.id}>
            <div className="flex-1">
              <p className="font-medium" style={{ color: "var(--color-ink)" }}>{e.description}</p>
              <p className="text-xs font-mono mt-1" style={{ color: "var(--color-ink-soft)" }}>
                Project #{e.project_id} · captured {formatDateTime(e.captured_at)}
              </p>
              {e.image_url && (
                <a href={e.image_url} target="_blank" rel="noreferrer" className="text-xs font-medium underline" style={{ color: "var(--color-marigold-deep)" }}>
                  View photo
                </a>
              )}
              {(e.ai_stage || e.confirming_citizens != null || e.ai_reason) && (
                <div className="mt-2 flex flex-wrap gap-2">
                  {e.ai_stage && (
                    <EvidenceBadge>Stage: {e.ai_stage}{e.ai_stage_completion ? ` · ${e.ai_stage_completion.toLowerCase()}` : ""}</EvidenceBadge>
                  )}
                  {e.confirming_citizens != null && (
                    <EvidenceBadge>{e.confirming_citizens} confirming {e.confirming_citizens === 1 ? "citizen" : "citizens"}</EvidenceBadge>
                  )}
                  {e.activity_score != null && (
                    <EvidenceBadge>Activity score {e.activity_score.toFixed(2)}</EvidenceBadge>
                  )}
                </div>
              )}
              {e.ai_reason && (
                <p className="text-xs italic mt-1.5" style={{ color: "var(--color-ink-soft)" }}>"{e.ai_reason}"</p>
              )}
            </div>
            <div className="flex gap-2 shrink-0">
              <ActionButton variant="green" onClick={() => approve(e.id)} disabled={busyId === e.id}>Approve</ActionButton>
              <ActionButton variant="red" onClick={() => reject(e.id)} disabled={busyId === e.id}>Reject</ActionButton>
            </div>
          </Card>
        ))}
      </Section>

      <Section title="Reviewed">
        {reviewed.map((e) => (
          <Card key={e.id}>
            <div className="flex-1">
              <p className="font-medium" style={{ color: "var(--color-ink)" }}>{e.description}</p>
              <p className="text-xs font-mono mt-1" style={{ color: "var(--color-ink-soft)" }}>{formatDateTime(e.updated_at)}</p>
            </div>
            <Stamp status={e.status} size="sm" />
          </Card>
        ))}
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div className="mb-10">
      <h2 className="text-xs font-mono uppercase tracking-widest mb-3" style={{ color: "var(--color-ink-soft)" }}>{title}</h2>
      <div className="space-y-3">{children}</div>
    </div>
  );
}

function Card({ children }) {
  return (
    <div className="flex items-start justify-between gap-4 p-4 rounded-lg border" style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}>
      {children}
    </div>
  );
}

function Empty({ children }) {
  return <p className="text-sm" style={{ color: "var(--color-ink-soft)" }}>{children}</p>;
}

function EvidenceBadge({ children }) {
  return (
    <span
      className="text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded"
      style={{ color: "var(--color-marigold-deep)", backgroundColor: "var(--color-paper)", border: "1px solid var(--color-line)" }}
    >
      {children}
    </span>
  );
}

function ActionButton({ variant, children, ...props }) {
  const color = variant === "green" ? "var(--color-stamp-green)" : "var(--color-stamp-red)";
  return (
    <button
      {...props}
      className="text-xs font-semibold uppercase tracking-wide px-3 py-1.5 rounded border disabled:opacity-50"
      style={{ borderColor: color, color }}
    >
      {children}
    </button>
  );
}
