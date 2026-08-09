import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { formatBudget } from "../lib/format";
import { Stamp } from "../components/Stamp";

export default function Home() {
  const [projects, setProjects] = useState(null);

  useEffect(() => {
    api.listProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  const stats = projects
    ? {
        total: projects.length,
        totalBudget: projects.reduce((sum, p) => sum + (p.budget || 0), 0),
        avgProgress: Math.round(
          projects.reduce((sum, p) => sum + p.progress_percent, 0) / (projects.length || 1)
        ),
        delivered: projects.filter((p) => p.status === "COMPLETED").length,
      }
    : null;

  return (
    <div>
      {/* Hero: the ledger's opening page */}
      <section className="paper-grain border-b-2" style={{ borderColor: "var(--color-ink)" }}>
        <div className="max-w-6xl mx-auto px-6 py-20 sm:py-28">
          <p className="font-mono text-xs uppercase tracking-[0.25em] mb-5" style={{ color: "var(--color-marigold-deep)" }}>
            Government of Karnataka · Public Ledger, Vol. I
          </p>
          <h1 className="font-display text-4xl sm:text-6xl leading-[1.05] max-w-3xl" style={{ color: "var(--color-ink)" }}>
            Every crore promised. <br />
            <span className="italic">Every crore, tracked.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base sm:text-lg" style={{ color: "var(--color-ink-soft)" }}>
            A public record comparing what Karnataka's budget promised for roads and
            government schools against what citizens can actually verify on the ground —
            photographed, timestamped, and stamped permanently onto a public blockchain.
          </p>
          <div className="mt-9 flex flex-wrap items-center gap-4">
            <Link
              to="/projects"
              className="px-6 py-3 rounded font-semibold text-white shadow-sm"
              style={{ backgroundColor: "var(--color-ink)" }}
            >
              Open the Register →
            </Link>
            <Link
              to="/propose"
              className="px-6 py-3 rounded font-semibold border-2"
              style={{ borderColor: "var(--color-ink)", color: "var(--color-ink)" }}
            >
              Propose a Project
            </Link>
          </div>
        </div>
      </section>

      {/* Ledger summary strip */}
      <section className="border-b" style={{ borderColor: "var(--color-line)" }}>
        <div className="max-w-6xl mx-auto px-6 py-10 grid grid-cols-2 sm:grid-cols-4 gap-8">
          <StatBlock label="Projects tracked" value={stats ? stats.total : "—"} />
          <StatBlock label="Public funds in ledger" value={stats ? formatBudget(stats.totalBudget) : "—"} />
          <StatBlock label="Average completion" value={stats ? `${stats.avgProgress}%` : "—"} />
          <StatBlock label="Fully delivered" value={stats ? stats.delivered : "—"} />
        </div>
      </section>

      {/* Recent entries */}
      <section className="max-w-6xl mx-auto px-6 py-16">
        <div className="flex items-baseline justify-between mb-8">
          <h2 className="font-display text-2xl" style={{ color: "var(--color-ink)" }}>
            Latest entries in the register
          </h2>
          <Link to="/projects" className="text-sm font-medium" style={{ color: "var(--color-marigold-deep)" }}>
            View all →
          </Link>
        </div>

        {!projects && <p style={{ color: "var(--color-ink-soft)" }}>Reading the ledger…</p>}
        {projects && projects.length === 0 && (
          <p style={{ color: "var(--color-ink-soft)" }}>No projects have been entered into the register yet.</p>
        )}

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects?.slice(0, 6).map((p) => (
            <Link
              key={p.id}
              to={`/projects/${p.id}`}
              className="block p-5 rounded-lg border bg-white hover:shadow-md transition-shadow"
              style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}
            >
              <div className="flex items-start justify-between gap-3 mb-3">
                <h3 className="font-display text-lg leading-snug" style={{ color: "var(--color-ink)" }}>
                  {p.name}
                </h3>
                <Stamp status={p.status} size="sm" tilt={-4} />
              </div>
              <p className="text-sm mb-3" style={{ color: "var(--color-ink-soft)" }}>{p.location_name}</p>
              <ProgressBar value={p.progress_percent} />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatBlock({ label, value }) {
  return (
    <div>
      <p className="font-mono text-3xl font-semibold" style={{ color: "var(--color-ink)" }}>{value}</p>
      <p className="text-xs uppercase tracking-wider mt-1" style={{ color: "var(--color-ink-soft)" }}>{label}</p>
    </div>
  );
}

export function ProgressBar({ value }) {
  return (
    <div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ backgroundColor: "var(--color-line)" }}>
        <div
          className="h-full rounded-full"
          style={{
            width: `${Math.min(100, Math.max(0, value))}%`,
            backgroundColor: value >= 70 ? "var(--color-stamp-green)" : value >= 30 ? "var(--color-marigold)" : "var(--color-stamp-red)",
          }}
        />
      </div>
      <p className="text-xs font-mono mt-1" style={{ color: "var(--color-ink-soft)" }}>{value}% complete</p>
    </div>
  );
}
