// Every call goes through /api/*, which Vite proxies to FastAPI in dev
// (see vite.config.js) and which FastAPI serves directly in production
// since it's the same origin as the built app. No environment-specific
// base URL to configure.
const API_BASE = "/api";

function getToken() {
  return localStorage.getItem("pvp_token");
}

export function setToken(token) {
  if (token) localStorage.setItem("pvp_token", token);
  else localStorage.removeItem("pvp_token");
}

class ApiError extends Error {
  constructor(message, status, detail) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

async function request(path, { method = "GET", body, form, auth = true } = {}) {
  const headers = {};
  if (body) headers["Content-Type"] = "application/json";
  if (form) headers["Content-Type"] = "application/x-www-form-urlencoded";

  if (auth) {
    const token = getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: form ? form : body ? JSON.stringify(body) : undefined,
  });

  // 204/empty responses (rare here, but don't choke on them)
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map((d) => d.msg).join(", ")
      : detail || `Request failed (${res.status})`;
    throw new ApiError(message, res.status, detail);
  }

  return data;
}

export const api = {
  // --- auth ---
  register: (payload) => request("/auth/register", { method: "POST", body: payload, auth: false }),
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return request("/auth/login", { method: "POST", form, auth: false });
  },
  me: () => request("/auth/me"),

  // --- projects ---
  listProjects: () => request("/projects/", { auth: false }),
  getProject: (id) => request(`/projects/${id}`, { auth: false }),

  // --- proposals ---
  listProposals: () => request("/proposals/"),
  createProposal: (payload) => request("/proposals/", { method: "POST", body: payload }),
  approveProposal: (id) => request(`/proposals/approve/${id}`, { method: "PUT" }),
  rejectProposal: (id, reason) => request(`/proposals/reject/${id}`, { method: "PUT", body: { reason } }),

  // --- evidence ---
  listEvidence: () => request("/evidence/"),
  getProjectEvidence: (projectId) => request(`/evidence/project/${projectId}`, { auth: false }),
  uploadEvidence: (payload) => request("/evidence/", { method: "POST", body: payload }),
  approveEvidence: (id) => request(`/evidence/approve/${id}`, { method: "PUT" }),
  rejectEvidence: (id, reason) => request(`/evidence/reject/${id}`, { method: "PUT", body: { reason } }),

  // --- blockchain ---
  getProjectRecords: (projectId) => request(`/blockchain/projects/${projectId}/records`, { auth: false }),
  verifyHash: (dataHash) => request("/blockchain/verify", { method: "POST", body: { data_hash: dataHash }, auth: false }),
};

export { ApiError };
