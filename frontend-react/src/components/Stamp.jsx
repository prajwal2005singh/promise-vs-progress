// The signature element of this design: every status in the app --
// a project's delivery state, a piece of evidence's review state, a
// blockchain record's confirmation state -- reads as an ink stamp, the
// way a physical government file gets stamped "APPROVED" or "PENDING".
// It's rendered as an SVG so the ink-edge roughness (feTurbulence
// displacement) is real, not a drop-shadow trick.

const VARIANTS = {
  green: { fill: "var(--color-stamp-green)" },
  red: { fill: "var(--color-stamp-red)" },
  marigold: { fill: "var(--color-marigold-deep)" },
  ink: { fill: "var(--color-ink-soft)" },
};

// Central place mapping every status string used across projects,
// evidence, and proposals to a label + ink color, so a new status only
// needs to be added once.
const STATUS_MAP = {
  // Project delivery status
  PLANNING: { label: "Planning", variant: "ink" },
  APPROVED: { label: "Approved", variant: "marigold" },
  ONGOING: { label: "Ongoing", variant: "marigold" },
  DELAYED: { label: "Delayed", variant: "red" },
  STALLED: { label: "Stalled", variant: "red" },
  COMPLETED: { label: "Delivered", variant: "green" },
  // Evidence / proposal review status
  PENDING: { label: "Pending Review", variant: "ink" },
  REJECTED: { label: "Rejected", variant: "red" },
  // Blockchain record status
  CONFIRMED: { label: "Confirmed", variant: "green" },
  FAILED: { label: "Anchor Failed", variant: "red" },
};

let uid = 0;

export function Stamp({ status, label, size = "md", tilt = -6 }) {
  const meta = STATUS_MAP[status] || { label: status, variant: "ink" };
  const text = label || meta.label;
  const color = VARIANTS[meta.variant].fill;
  const filterId = `stamp-rough-${uid++}`;

  const sizes = {
    sm: { px: "px-2.5 py-1", text: "text-[10px]", tracking: "tracking-wider" },
    md: { px: "px-3.5 py-1.5", text: "text-xs", tracking: "tracking-widest" },
    lg: { px: "px-5 py-2", text: "text-sm", tracking: "tracking-widest" },
  };
  const s = sizes[size];

  return (
    <span
      className={`relative inline-flex items-center justify-center ${s.px} ${s.text} ${s.tracking} font-mono font-semibold uppercase select-none whitespace-nowrap`}
      style={{
        color,
        transform: `rotate(${tilt}deg)`,
        border: `2px solid ${color}`,
        borderRadius: "3px",
        filter: `url(#${filterId})`,
        opacity: 0.92,
      }}
    >
      <svg width="0" height="0" style={{ position: "absolute" }}>
        <filter id={filterId}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="1.6" />
        </filter>
      </svg>
      {text}
    </span>
  );
}
