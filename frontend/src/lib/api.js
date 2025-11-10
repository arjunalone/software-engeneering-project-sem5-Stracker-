const BACKEND = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function apiRequest(endpoint, options = {}) {
  const url = `${BACKEND}${endpoint}`;
  try {
    const res = await fetch(url, options);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      return { error: errorData.error || errorData.message || `HTTP ${res.status}`, status: res.status };
    }
    if (res.status === 204 || options.method === "DELETE") return { success: true };
    return await res.json();
  } catch (err) {
    return { error: err.message || "Network error" };
  }
}

export const register = (name, email, password, role = "user", adminSecret = "") =>
  apiRequest("/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, role, admin_secret: adminSecret })
  });
export const login = (email, password, asRole = "") =>
  apiRequest("/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, as_role: asRole })
  });
export const me = (token) => apiRequest("/me", { headers: { Authorization: `Bearer ${token}` } });

export const getReleases = (token) => apiRequest("/releases", { headers: { Authorization: `Bearer ${token}` } });
export const createRelease = (token, project_name, version, status) =>
  apiRequest("/releases", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ project_name, version, status }) });
export const updateReleaseStatus = (token, releaseId, status) =>
  apiRequest(`/releases/${releaseId}`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ status }) });
export const deleteRelease = (token, releaseId) =>
  apiRequest(`/releases/${releaseId}`, { method: "DELETE", headers: { Authorization: `Bearer ${token}` } });

export const scanFile = (token, file) => {
  const formData = new FormData();
  formData.append("file", file);
  return apiRequest("/scan", { method: "POST", headers: { Authorization: `Bearer ${token}` }, body: formData });
};

export const importScanResults = (token, rows, status = "Planned") =>
  apiRequest("/releases/import-scan", { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ rows, status }) });

// Admin API
export const adminListUsers = (token) =>
  apiRequest("/admin/users", { headers: { Authorization: `Bearer ${token}` } });

export const adminSetUserRole = (token, userId, role) =>
  apiRequest(`/admin/users/${userId}/role`, { method: "PATCH", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ role }) });
