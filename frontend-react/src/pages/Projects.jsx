import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { api } from "../lib/api";
import { formatBudget } from "../lib/format";
import { Stamp } from "../components/Stamp";
import { ProgressBar } from "./Home";

// Leaflet's default marker icons reference image files by relative
// path, which breaks under Vite's bundling. Rebuilding the icon from
// the installed package's own assets avoids the classic "broken marker
// image" bug entirely.
const markerIcon = new L.Icon({
  iconUrl: new URL("leaflet/dist/images/marker-icon.png", import.meta.url).href,
  iconRetinaUrl: new URL("leaflet/dist/images/marker-icon-2x.png", import.meta.url).href,
  shadowUrl: new URL("leaflet/dist/images/marker-shadow.png", import.meta.url).href,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
});

const KARNATAKA_CENTER = [14.5, 76.0];

export default function Projects() {
  const [projects, setProjects] = useState(null);
  const [error, setError] = useState(null);
  const [category, setCategory] = useState("ALL");
  const [status, setStatus] = useState("ALL");
  const [query, setQuery] = useState("");
  const [showMap, setShowMap] = useState(true);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((e) => setError(e.message));
  }, []);

  const categories = useMemo(
    () => (projects ? ["ALL", ...new Set(projects.map((p) => p.category))] : ["ALL"]),
    [projects]
  );
  const statuses = useMemo(
    () => (projects ? ["ALL", ...new Set(projects.map((p) => p.status))] : ["ALL"]),
    [projects]
  );

  const filtered = useMemo(() => {
    if (!projects) return [];
    return projects.filter((p) => {
      if (category !== "ALL" && p.category !== category) return false;
      if (status !== "ALL" && p.status !== status) return false;
      if (query && !`${p.name} ${p.location_name} ${p.constituency ?? ""}`.toLowerCase().includes(query.toLowerCase())) return false;
      return true;
    });
  }, [projects, category, status, query]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-12">
      <div className="mb-8">
        <p className="font-mono text-xs uppercase tracking-[0.25em] mb-2" style={{ color: "var(--color-marigold-deep)" }}>
          The Register
        </p>
        <h1 className="font-display text-3xl" style={{ color: "var(--color-ink)" }}>
          Karnataka infrastructure projects
        </h1>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 mb-6">
        <input
          type="text"
          placeholder="Search by name, place, or constituency…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="px-3 py-2 rounded border text-sm flex-1 min-w-[220px]"
          style={{ borderColor: "var(--color-line)", backgroundColor: "white" }}
        />
        <Select value={category} onChange={setCategory} options={categories} />
        <Select value={status} onChange={setStatus} options={statuses} />
        <button
          onClick={() => setShowMap((s) => !s)}
          className="text-sm font-medium px-3 py-2 rounded border"
          style={{ borderColor: "var(--color-line)", color: "var(--color-ink-soft)" }}
        >
          {showMap ? "Hide map" : "Show map"}
        </button>
      </div>

      {error && (
        <p className="mb-6 text-sm px-4 py-3 rounded" style={{ backgroundColor: "#FBEAE6", color: "var(--color-stamp-red)" }}>
          Couldn't reach the register: {error}
        </p>
      )}

      {showMap && filtered.length > 0 && (
        <div className="mb-8 rounded-lg overflow-hidden border" style={{ borderColor: "var(--color-line)", height: 360 }}>
          <MapContainer center={KARNATAKA_CENTER} zoom={7} style={{ height: "100%", width: "100%" }}>
            <TileLayer
              attribution='&copy; OpenStreetMap contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {filtered.map((p) => (
              <Marker key={p.id} position={[p.latitude, p.longitude]} icon={markerIcon}>
                <Popup>
                  <div className="font-body">
                    <p className="font-semibold mb-1">{p.name}</p>
                    <p className="text-xs mb-2">{p.location_name}</p>
                    <Link to={`/projects/${p.id}`} className="text-xs font-medium underline">
                      View details →
                    </Link>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        </div>
      )}

      {!projects && !error && <p style={{ color: "var(--color-ink-soft)" }}>Reading the ledger…</p>}

      {projects && filtered.length === 0 && (
        <p style={{ color: "var(--color-ink-soft)" }}>No entries match those filters.</p>
      )}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
        {filtered.map((p) => (
          <Link
            key={p.id}
            to={`/projects/${p.id}`}
            className="block p-5 rounded-lg border bg-white hover:shadow-md transition-shadow"
            style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className="font-display text-lg leading-snug" style={{ color: "var(--color-ink)" }}>
                {p.name}
              </h3>
              <Stamp status={p.status} size="sm" tilt={-4} />
            </div>
            <p className="text-xs uppercase tracking-wider font-mono mb-1" style={{ color: "var(--color-marigold-deep)" }}>
              {p.category} · {p.department}
            </p>
            <p className="text-sm mb-3" style={{ color: "var(--color-ink-soft)" }}>{p.location_name}</p>
            <p className="text-sm font-mono mb-3" style={{ color: "var(--color-ink)" }}>{formatBudget(p.budget)}</p>
            <ProgressBar value={p.progress_percent} />
          </Link>
        ))}
      </div>
    </div>
  );
}

function Select({ value, onChange, options }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="px-3 py-2 rounded border text-sm"
      style={{ borderColor: "var(--color-line)", backgroundColor: "white", color: "var(--color-ink)" }}
    >
      {options.map((o) => (
        <option key={o} value={o}>
          {o === "ALL" ? "All" : o.charAt(0) + o.slice(1).toLowerCase()}
        </option>
      ))}
    </select>
  );
}
