/**
 * Base Axios client for all Verilab API calls.
 * Reads base URL from VITE_API_BASE_URL env var (defaults to localhost:8000).
 */

import axios from "axios";

const BASE_URL = (typeof window !== "undefined" && (import.meta as any).env?.VITE_API_BASE_URL) ?? "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor — attach auth token from localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("verilab_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — surface errors consistently
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message =
      error.response?.data?.detail ?? error.message ?? "Unknown error";
    return Promise.reject(new Error(message));
  }
);

// Default export for any legacy imports that use `import api from ...`
export default apiClient;
