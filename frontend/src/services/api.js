const API_BASE = import.meta.env.VITE_API_URL;

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (!path.includes("/api/auth/login") && !path.includes("/api/auth/register")) {
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });
}