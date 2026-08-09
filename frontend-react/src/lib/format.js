// Budgets in the DB are stored in raw rupees (integers), matching how
// Indian government budget announcements are usually reported in
// crore (1 crore = 1,00,00,000). Converting for display here keeps the
// backend's integer column simple while showing numbers the way a
// citizen actually reads them ("₹1,778 Cr", not "₹17,780,000,000").
export function formatBudget(rupees) {
  if (rupees == null) return "Not disclosed";
  const crore = rupees / 1e7;
  if (crore >= 100) return `₹${Math.round(crore).toLocaleString("en-IN")} Cr`;
  return `₹${crore.toLocaleString("en-IN", { maximumFractionDigits: 1 })} Cr`;
}

export function formatDate(iso) {
  if (!iso) return "Not set";
  return new Date(iso).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function shortHash(hash, chars = 8) {
  if (!hash) return "—";
  return `${hash.slice(0, chars + 2)}…${hash.slice(-6)}`;
}

// Whether a project is behind its own promised schedule, purely from
// dates + progress -- used to flag "Delayed" even when an admin hasn't
// manually set that status yet.
export function isBehindSchedule(project) {
  if (!project.expected_completion || project.status === "COMPLETED") return false;
  const today = new Date();
  const due = new Date(project.expected_completion);
  return due < today && project.progress_percent < 100;
}
