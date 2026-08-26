import { useEffect, useMemo, useState } from "react";
import L from "leaflet";
import {
  CircleMarker,
  GeoJSON,
  MapContainer,
  Popup,
  TileLayer,
  useMap,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";

function FitGeometry({ geometry, fallbackCenter }) {
  const map = useMap();

  useEffect(() => {
    if (geometry?.coordinates) {
      const layer = L.geoJSON(geometry);
      if (layer) {
        map.fitBounds(layer.getBounds(), { padding: [28, 28] });
      }
    } else if (fallbackCenter) {
      map.setView(fallbackCenter, 12);
    }
  }, [geometry, fallbackCenter, map]);

  return null;
}

function flattenCoordinates(geometry) {
  if (!geometry?.coordinates) return [];

  const points = [];

  const walk = (value) => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === "number" && typeof value[1] === "number") {
      points.push([value[1], value[0]]);
      return;
    }
    value.forEach(walk);
  };

  walk(geometry.coordinates);
  return points;
}

function GeometryBadge({ status, source, confidence }) {
  const normalized = (status || "UNAVAILABLE").toUpperCase();
  const style = normalized === "VERIFIED"
    ? {
        color: "var(--color-stamp-green)",
        backgroundColor: "rgba(47,110,82,0.10)",
        borderColor: "rgba(47,110,82,0.30)",
      }
    : normalized === "ESTIMATED"
      ? {
          color: "var(--color-marigold-deep)",
          backgroundColor: "rgba(217,142,31,0.10)",
          borderColor: "rgba(217,142,31,0.30)",
        }
      : {
          color: "var(--color-ink-soft)",
          backgroundColor: "var(--color-paper)",
          borderColor: "var(--color-line)",
        };

  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      <span
        className="px-2 py-1 rounded border font-mono uppercase tracking-wider"
        style={style}
      >
        Geometry: {normalized}
      </span>
      {source && (
        <span style={{ color: "var(--color-ink-soft)" }}>
          {source}
        </span>
      )}
      {confidence != null && (
        <span style={{ color: "var(--color-ink-soft)" }}>
          {(confidence * 100).toFixed(0)}% confidence
        </span>
      )}
    </div>
  );
}

export default function ProjectMap({
  project,
  geometryRecord,
  onEstimate,
  estimating = false,
  isAdmin = false,
}) {
  const geometry = geometryRecord?.geometry || project?.location_geometry || null;
  const status = geometryRecord?.status || project?.location_geometry_status || null;
  const source = geometryRecord?.source || project?.location_geometry_source || null;
  const confidence = geometryRecord?.confidence ?? project?.location_geometry_confidence ?? null;
  const estimatedLength = geometryRecord?.estimated_length_km ?? project?.location_geometry_length_km ?? null;

  const fallbackCenter = useMemo(
    () => [Number(project.latitude), Number(project.longitude)],
    [project.latitude, project.longitude]
  );

  const geometryPoints = useMemo(
    () => flattenCoordinates(geometry),
    [geometry]
  );

  const bounds = useMemo(() => {
    if (geometryPoints.length < 2) return null;
    return geometryPoints;
  }, [geometryPoints]);

  const [mapReady, setMapReady] = useState(false);

  // React-Leaflet's GeoJSON layer is sufficient for rendering. This state
  // just gives the user a small visual cue while the map initializes.
  useEffect(() => setMapReady(true), []);

  return (
    <section
      className="mb-12 rounded-lg border overflow-hidden"
      style={{ borderColor: "var(--color-line)", backgroundColor: "var(--color-paper-raised)" }}
    >
      <div className="p-5 sm:p-6 border-b" style={{ borderColor: "var(--color-line)" }}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p
              className="font-mono text-xs uppercase tracking-widest mb-2"
              style={{ color: "var(--color-ink-soft)" }}
            >
              Project location
            </p>
            <h2 className="font-display text-2xl" style={{ color: "var(--color-ink)" }}>
              Corridor &amp; evidence map
            </h2>
            <p className="text-sm mt-1 max-w-2xl" style={{ color: "var(--color-ink-soft)" }}>
              Estimated corridors are derived from project metadata and road-network routing. They are guidance for evidence matching, not official survey geometry.
            </p>
          </div>

          {isAdmin && !geometry && (
            <button
              type="button"
              onClick={onEstimate}
              disabled={estimating}
              className="px-3 py-2 rounded border text-sm font-medium disabled:opacity-50"
              style={{
                borderColor: "var(--color-line)",
                color: "var(--color-ink)",
                backgroundColor: "white",
              }}
            >
              {estimating ? "Estimating…" : "Estimate corridor"}
            </button>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2">
          <GeometryBadge status={status} source={source} confidence={confidence} />
          {estimatedLength != null && (
            <span className="text-xs font-mono" style={{ color: "var(--color-ink-soft)" }}>
              Estimated length: {Number(estimatedLength).toFixed(2)} km
            </span>
          )}
        </div>
      </div>

      <div className="relative">
        {!mapReady && (
          <div className="absolute inset-0 z-10 flex items-center justify-center text-sm" style={{ color: "var(--color-ink-soft)", backgroundColor: "var(--color-paper-raised)" }}>
            Loading map…
          </div>
        )}

        <MapContainer
          center={fallbackCenter}
          zoom={12}
          scrollWheelZoom={false}
          className="pvp-project-map"
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {geometry && (
            <GeoJSON
              key={JSON.stringify(geometry)}
              data={geometry}
              style={() => ({
                color: status === "VERIFIED" ? "#2F6E52" : "#B5720F",
                weight: 5,
                opacity: 0.9,
              })}
              onEachFeature={(_, layer) => {
                layer.bindPopup(
                  `<strong>${project.name}</strong><br/>${status === "VERIFIED" ? "Verified geometry" : "Estimated geometry"}`
                );
              }}
            />
          )}

          <CircleMarker
            center={fallbackCenter}
            radius={6}
            pathOptions={{
              color: "#1C2541",
              fillColor: "#1C2541",
              fillOpacity: 0.95,
              weight: 2,
            }}
          >
            <Popup>
              <strong>{project.name}</strong>
              <br />
              Project reference point
            </Popup>
          </CircleMarker>

          <FitGeometry geometry={geometry} fallbackCenter={fallbackCenter} />
        </MapContainer>
      </div>

      <div className="px-5 py-4 sm:px-6 border-t grid sm:grid-cols-3 gap-4 text-xs" style={{ borderColor: "var(--color-line)" }}>
        <div>
          <p className="font-mono uppercase tracking-wider mb-1" style={{ color: "var(--color-ink-soft)" }}>
            Reference point
          </p>
          <p className="font-mono" style={{ color: "var(--color-ink)" }}>
            {Number(project.latitude).toFixed(5)}, {Number(project.longitude).toFixed(5)}
          </p>
        </div>

        <div>
          <p className="font-mono uppercase tracking-wider mb-1" style={{ color: "var(--color-ink-soft)" }}>
            Location mode
          </p>
          <p style={{ color: "var(--color-ink)" }}>
            {geometry ? "Corridor / project geometry" : "Reference point fallback"}
          </p>
        </div>

        <div>
          <p className="font-mono uppercase tracking-wider mb-1" style={{ color: "var(--color-ink-soft)" }}>
            Routing basis
          </p>
          <p style={{ color: "var(--color-ink)" }}>
            {bounds ? "Road-network route" : "Project coordinates"}
          </p>
        </div>
      </div>
    </section>
  );
}
