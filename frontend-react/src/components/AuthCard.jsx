export default function AuthCard({ title, subtitle, children }) {
  return (
    <div className="max-w-md mx-auto px-6 py-16">
      <div className="p-8 rounded-lg border-2" style={{ borderColor: "var(--color-ink)", backgroundColor: "var(--color-paper-raised)" }}>
        <h1 className="font-display text-2xl mb-1" style={{ color: "var(--color-ink)" }}>{title}</h1>
        {subtitle && <p className="text-sm mb-6" style={{ color: "var(--color-ink-soft)" }}>{subtitle}</p>}
        {children}
      </div>
    </div>
  );
}

export function Field({ label, ...props }) {
  return (
    <label className="block mb-4">
      <span className="block text-xs font-mono uppercase tracking-wider mb-1.5" style={{ color: "var(--color-ink-soft)" }}>
        {label}
      </span>
      <input
        {...props}
        className="w-full px-3 py-2.5 rounded border text-sm"
        style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
      />
    </label>
  );
}

export function SubmitButton({ children, ...props }) {
  return (
    <button
      {...props}
      className="w-full py-2.5 rounded font-semibold text-white mt-2 disabled:opacity-60"
      style={{ backgroundColor: "var(--color-ink)" }}
    >
      {children}
    </button>
  );
}

export function ErrorText({ children }) {
  if (!children) return null;
  return (
    <p className="text-sm mt-3 px-3 py-2 rounded" style={{ backgroundColor: "#FBEAE6", color: "var(--color-stamp-red)" }}>
      {children}
    </p>
  );
}
