import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../lib/api";
import {
  formatBudget,
  formatDate,
  formatDateTime,
  shortHash,
  isBehindSchedule,
} from "../lib/format";
import { Stamp } from "../components/Stamp";
import { ProgressBar } from "./Home";
import { useAuth } from "../context/AuthContext";
import ProjectMap from "../components/ProjectMap";

const RECORD_TYPE_LABEL = {
  EVIDENCE: "Evidence submitted",
  VERIFIED_PROGRESS: "Evidence verified",
  AUDIT_UPDATE: "Project status updated",
};

export default function ProjectDetail() {
  const { id } = useParams();

  const [project, setProject] = useState(null);
  const [evidence, setEvidence] = useState(null);
  const [records, setRecords] = useState(null);

  // Dynamically calculated project progress
  const [progress, setProgress] = useState(null);

  const [geometry, setGeometry] = useState(null);
  const [geometryLoading, setGeometryLoading] = useState(true);
  const [geometryError, setGeometryError] = useState(null);
  const [estimatingGeometry, setEstimatingGeometry] = useState(false);

  const [error, setError] = useState(null);

  const { user } = useAuth();

  useEffect(() => {
    setProject(null);
    setEvidence(null);
    setRecords(null);
    setProgress(null);
    setGeometry(null);

    setGeometryLoading(true);
    setGeometryError(null);
    setError(null);

    api
      .getProject(id)
      .then(setProject)
      .catch((e) => setError(e.message));

    api
      .getProjectEvidence(id)
      .then(setEvidence)
      .catch(() => setEvidence([]));

    api
      .getProjectRecords(id)
      .then(setRecords)
      .catch(() => setRecords([]));

    // Progress is calculated dynamically by the backend Progress Engine.
    api
      .getProjectProgress(id)
      .then(setProgress)
      .catch(() => setProgress(null));

    api
      .getProjectGeometry(id)
      .then(setGeometry)
      .catch((e) => setGeometryError(e.message))
      .finally(() => setGeometryLoading(false));
  }, [id]);

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-16 text-center">
        <p style={{ color: "var(--color-stamp-red)" }}>
          This project isn't in the register: {error}
        </p>

        <Link
          to="/projects"
          className="inline-block mt-4 text-sm font-medium"
          style={{ color: "var(--color-marigold-deep)" }}
        >
          ← Back to the register
        </Link>
      </div>
    );
  }

  if (!project) {
    return (
      <p
        className="max-w-6xl mx-auto px-6 py-16"
        style={{ color: "var(--color-ink-soft)" }}
      >
        Reading the file…
      </p>
    );
  }

  const behind = isBehindSchedule(project);

  const progressCalculated =
    progress?.status === "CALCULATED" &&
    typeof progress.project_progress_percent === "number";

  return (
    <div className="max-w-5xl mx-auto px-6 py-12">
      <Link
        to="/projects"
        className="text-sm font-medium"
        style={{ color: "var(--color-marigold-deep)" }}
      >
        ← Register
      </Link>

      {/* Case-file header */}
      <div
        className="mt-4 mb-10 pb-8 border-b-2"
        style={{ borderColor: "var(--color-ink)" }}
      >
        <div className="flex flex-wrap items-start justify-between gap-4 mb-3">
          <h1
            className="font-display text-3xl sm:text-4xl max-w-2xl"
            style={{ color: "var(--color-ink)" }}
          >
            {project.name}
          </h1>

          <Stamp status={project.status} size="lg" />
        </div>

        <p
          className="text-sm font-mono uppercase tracking-wider mb-4"
          style={{ color: "var(--color-marigold-deep)" }}
        >
          {project.category} · {project.department}
          {project.constituency ? ` · ${project.constituency}` : ""}
        </p>

        <p
          className="text-base max-w-2xl"
          style={{ color: "var(--color-ink-soft)" }}
        >
          {project.description}
        </p>

        {behind && (
          <p
            className="mt-3 text-sm font-medium"
            style={{ color: "var(--color-stamp-red)" }}
          >
            ⚠ Past its promised completion date and not yet marked delivered.
          </p>
        )}
      </div>

      {/* Project GIS map */}
      {!geometryLoading && (
        <ProjectMap
          project={project}
          geometryRecord={geometry}
          isAdmin={user?.role === "ADMIN"}
          estimating={estimatingGeometry}
          onEstimate={async () => {
            setEstimatingGeometry(true);
            setGeometryError(null);

            try {
              await api.estimateProjectGeometry(id);

              const fresh = await api.getProjectGeometry(id);
              setGeometry(fresh);
            } catch (e) {
              setGeometryError(e.message);
            } finally {
              setEstimatingGeometry(false);
            }
          }}
        />
      )}

      {geometryError && (
        <p
          className="-mt-8 mb-8 text-xs"
          style={{ color: "var(--color-stamp-red)" }}
        >
          GIS note: {geometryError}
        </p>
      )}

      {/* Promise vs Progress */}
      <div className="grid sm:grid-cols-2 gap-6 mb-12">
        {/* Promise */}
        <div
          className="p-6 rounded-lg border"
          style={{
            borderColor: "var(--color-line)",
            backgroundColor: "var(--color-paper-raised)",
          }}
        >
          <p
            className="font-mono text-xs uppercase tracking-widest mb-3"
            style={{ color: "var(--color-ink-soft)" }}
          >
            The Promise
          </p>

          <dl className="space-y-2 text-sm">
            <Row
              label="Allocated budget"
              value={formatBudget(project.budget)}
            />

            <Row
              label="Location"
              value={project.location_name}
            />

            <Row
              label="Start date"
              value={formatDate(project.start_date)}
            />

            <Row
              label="Expected completion"
              value={formatDate(project.expected_completion)}
            />
          </dl>
        </div>

        {/* Progress */}
        <div
          className="p-6 rounded-lg border"
          style={{
            borderColor: "var(--color-line)",
            backgroundColor: "var(--color-paper-raised)",
          }}
        >
          <div className="flex items-start justify-between gap-3 mb-3">
            <p
              className="font-mono text-xs uppercase tracking-widest"
              style={{ color: "var(--color-ink-soft)" }}
            >
              The Progress
            </p>

            {progressCalculated && (
              <span
                className="text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded"
                style={{
                  color: "var(--color-marigold-deep)",
                  backgroundColor: "var(--color-paper)",
                  border: "1px solid var(--color-line)",
                }}
              >
                Estimated
              </span>
            )}
          </div>

          {progressCalculated ? (
            <>
              <div className="mb-2">
                <ProgressBar
                  value={progress.project_progress_percent}
                />
              </div>

              <div
                className="text-right text-xs font-mono mb-4"
                style={{ color: "var(--color-ink-soft)" }}
              >
                {progress.project_progress_percent.toFixed(1)}%
              </div>
            </>
          ) : (
            <div
              className="p-4 rounded border mb-4 text-sm"
              style={{
                borderColor: "var(--color-line)",
                color: "var(--color-ink-soft)",
              }}
            >
              Progress unavailable — awaiting enough verified observations.
            </div>
          )}

          <dl className="space-y-2 text-sm">
            <Row
              label="Current status"
              value={
                <Stamp
                  status={project.status}
                  size="sm"
                  tilt={0}
                />
              }
            />

            <Row
              label="Verified observations"
              value={
                progress
                  ? progress.verified_observation_count
                  : "…"
              }
            />

            <Row
              label="Citizen-verified reports"
              value={
                evidence
                  ? evidence.length
                  : "…"
              }
            />

            {progressCalculated &&
              progress.schedule_progress_percent != null && (
                <Row
                  label="Schedule elapsed"
                  value={`${progress.schedule_progress_percent.toFixed(1)}%`}
                />
              )}

            {progressCalculated &&
              progress.schedule_status && (
                <Row
                  label="Schedule status"
                  value={progress.schedule_status}
                />
              )}

            <Row
              label="On-chain records"
              value={records ? records.length : "…"}
            />
          </dl>

          {progressCalculated && (
            <p
              className="text-xs mt-4"
              style={{ color: "var(--color-ink-soft)" }}
            >
              Calculated from verified observations using the current
              generic road-stage weights. This is not BOQ-derived progress.
            </p>
          )}

          {progress?.warnings?.length > 0 && (
            <div
              className="mt-4 p-3 rounded border text-xs"
              style={{
                borderColor: "var(--color-line)",
                color: "var(--color-ink-soft)",
              }}
            >
              {progress.warnings.map((warning, index) => (
                <p key={index}>
                  {warning}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Stage breakdown */}
      {progressCalculated &&
        progress.stage_progress &&
        Object.keys(progress.stage_progress).length > 0 && (
          <section className="mb-12">
            <h2
              className="font-display text-2xl mb-1"
              style={{ color: "var(--color-ink)" }}
            >
              Construction stage breakdown
            </h2>

            <p
              className="text-sm mb-6"
              style={{ color: "var(--color-ink-soft)" }}
            >
              Highest verified completion observed for each road-construction
              stage.
            </p>

            <div
              className="rounded-lg border overflow-hidden"
              style={{ borderColor: "var(--color-line)" }}
            >
              {Object.entries(progress.stage_progress).map(
                ([stage, value]) => (
                  <div
                    key={stage}
                    className="px-4 py-3 flex items-center justify-between gap-4 border-b last:border-b-0"
                    style={{ borderColor: "var(--color-line)" }}
                  >
                    <span
                      className="text-xs font-mono uppercase tracking-wider"
                      style={{ color: "var(--color-ink-soft)" }}
                    >
                      {stage.replaceAll("_", " ")}
                    </span>

                    <span
                      className="font-medium text-sm"
                      style={{ color: "var(--color-ink)" }}
                    >
                      {Number(value).toFixed(0)}%
                    </span>
                  </div>
                )
              )}
            </div>
          </section>
        )}

      {/* Evidence gallery */}
      <section className="mb-12">
        <h2
          className="font-display text-2xl mb-1"
          style={{ color: "var(--color-ink)" }}
        >
          Verified progress on the ground
        </h2>

        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Photos and reports automatically verified when the Image Engine is
          confident; uncertain observations are sent for human review.
        </p>

        {evidence && evidence.length === 0 && (
          <p
            className="text-sm p-5 rounded border"
            style={{
              borderColor: "var(--color-line)",
              color: "var(--color-ink-soft)",
            }}
          >
            No verified evidence yet.{" "}
            <Link
              to="/upload-evidence"
              className="font-medium underline"
            >
              Be the first to submit a progress report
            </Link>
            .
          </p>
        )}

        <div className="grid sm:grid-cols-2 gap-4">
          {evidence?.map((e) => (
            <div
              key={e.id}
              className="rounded-lg border overflow-hidden bg-white"
              style={{ borderColor: "var(--color-line)" }}
            >
              {e.image_url && (
                <img
                  src={e.image_url}
                  alt={e.description}
                  className="w-full h-44 object-cover"
                  onError={(ev) => {
                    ev.target.style.display = "none";
                  }}
                />
              )}

              <div className="p-4">
                <p
                  className="text-sm mb-2"
                  style={{ color: "var(--color-ink)" }}
                >
                  {e.description}
                </p>

                <p
                  className="text-xs font-mono mb-2"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  Captured {formatDate(e.captured_at)}
                </p>

                {(e.ai_stage ||
                  e.confirming_citizens != null) && (
                  <div className="flex flex-wrap gap-2">
                    {e.ai_stage && (
                      <Badge>
                        Stage: {e.ai_stage}
                        {e.ai_stage_completion
                          ? ` · ${e.ai_stage_completion.toLowerCase()}`
                          : ""}
                      </Badge>
                    )}

                    {e.confirming_citizens != null &&
                      e.confirming_citizens > 1 && (
                        <Badge>
                          Confirmed by {e.confirming_citizens} citizens
                        </Badge>
                      )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Blockchain audit trail */}
      <section>
        <h2
          className="font-display text-2xl mb-1"
          style={{ color: "var(--color-ink)" }}
        >
          On-chain audit trail
        </h2>

        <p
          className="text-sm mb-6"
          style={{ color: "var(--color-ink-soft)" }}
        >
          Every submission and verification below is anchored on the project
          audit chain. The record can be independently checked against the
          configured network.
        </p>

        {records && records.length === 0 && (
          <p
            className="text-sm p-5 rounded border"
            style={{
              borderColor: "var(--color-line)",
              color: "var(--color-ink-soft)",
            }}
          >
            Nothing has been anchored on-chain for this project yet.
          </p>
        )}

        <ol className="relative">
          {records?.map((r, i) => (
            <li
              key={r.id}
              className="pl-6 pb-6 relative"
              style={{
                borderLeft:
                  i === records.length - 1
                    ? "none"
                    : "2px solid var(--color-line)",
              }}
            >
              <span
                className="absolute -left-[7px] top-1 w-3 h-3 rounded-full"
                style={{
                  backgroundColor:
                    r.status === "CONFIRMED"
                      ? "var(--color-stamp-green)"
                      : r.status === "FAILED"
                        ? "var(--color-stamp-red)"
                        : "var(--color-marigold)",
                }}
              />

              <div className="flex flex-wrap items-center gap-2 mb-1">
                <p
                  className="font-medium text-sm"
                  style={{ color: "var(--color-ink)" }}
                >
                  {RECORD_TYPE_LABEL[r.record_type] ||
                    r.record_type}
                </p>

                <Stamp
                  status={r.status}
                  size="sm"
                  tilt={-3}
                />
              </div>

              <p
                className="text-xs font-mono"
                style={{ color: "var(--color-ink-soft)" }}
              >
                {formatDateTime(r.created_at)}
              </p>

              {r.tx_hash && (
                <p
                  className="text-xs font-mono mt-1 break-all"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  tx {shortHash(r.tx_hash)}
                  {r.block_number != null &&
                    ` · block ${r.block_number}`}
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt style={{ color: "var(--color-ink-soft)" }}>
        {label}
      </dt>

      <dd
        className="font-medium text-right"
        style={{ color: "var(--color-ink)" }}
      >
        {value}
      </dd>
    </div>
  );
}

function Badge({ children }) {
  return (
    <span
      className="text-[10px] font-mono uppercase tracking-wider px-2 py-1 rounded"
      style={{
        color: "var(--color-marigold-deep)",
        backgroundColor: "var(--color-paper)",
        border: "1px solid var(--color-line)",
      }}
    >
      {children}
    </span>
  );
}
