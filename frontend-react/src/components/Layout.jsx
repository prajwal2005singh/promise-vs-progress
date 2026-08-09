import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `text-sm font-medium tracking-wide transition-colors ${
          isActive ? "text-marigold-deep" : "text-ink-soft hover:text-ink"
        }`
      }
      style={({ isActive }) => ({
        color: isActive ? "var(--color-marigold-deep)" : undefined,
      })}
    >
      {children}
    </NavLink>
  );
}

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b-2" style={{ borderColor: "var(--color-ink)" }}>
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-6">
          <Link to="/" className="flex items-baseline gap-2 shrink-0">
            <span
              className="font-display text-xl font-semibold"
              style={{ color: "var(--color-ink)" }}
            >
              Promise <span style={{ color: "var(--color-marigold-deep)" }}>vs</span> Progress
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-7">
            <NavItem to="/projects">Register of Projects</NavItem>
            <NavItem to="/propose">Propose a Project</NavItem>
            {user && <NavItem to="/upload-evidence">Submit Evidence</NavItem>}
            {user?.role === "ADMIN" && <NavItem to="/admin">Admin Desk</NavItem>}
          </nav>

          <div className="flex items-center gap-3 shrink-0">
            {user ? (
              <>
                <span className="hidden sm:block text-xs font-mono uppercase tracking-wider" style={{ color: "var(--color-ink-soft)" }}>
                  {user.name.split(" ")[0]} · {user.role}
                </span>
                <button
                  onClick={logout}
                  className="text-sm font-medium px-3 py-1.5 rounded border"
                  style={{ borderColor: "var(--color-line)", color: "var(--color-ink-soft)" }}
                >
                  Sign out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-sm font-medium px-3 py-1.5"
                  style={{ color: "var(--color-ink-soft)" }}
                >
                  Log in
                </Link>
                <Link
                  to="/register"
                  className="text-sm font-semibold px-3.5 py-1.5 rounded text-white"
                  style={{ backgroundColor: "var(--color-ink)" }}
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t mt-16" style={{ borderColor: "var(--color-line)" }}>
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs" style={{ color: "var(--color-ink-soft)" }}>
          <p className="font-mono">Promise vs Progress · Karnataka Pilot · Roads &amp; Schools</p>
          <p className="font-mono">Every verified record is anchored on Polygon &mdash; nothing here can be quietly edited.</p>
        </div>
      </footer>
    </div>
  );
}
