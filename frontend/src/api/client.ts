/**
 * Base Axios client for all Verilab API calls.
 * Reads base URL from VITE_API_BASE_URL env var (defaults to localhost:8000).
 *
 * Free hosts (e.g. Render's free plan) put the backend to sleep when idle and
 * take ~30-60 s to wake. So we (1) start waking it the moment the page loads,
 * and (2) retry requests that fail because it is still starting, while a
 * "Starting server" banner is shown (see ServerWakeBanner).
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export const apiClient = axios.create({
  baseURL: BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// --- Waking a sleeping backend -------------------------------------------

export const SERVER_WAKING_EVENT = "verilab:server-waking";
const RETRY_DELAY_MS = 3000;
const MAX_WAIT_MS = 90_000;

let pending = 0;
function setWaking(delta: number) {
  const before = pending > 0;
  pending = Math.max(0, pending + delta);
  if (before !== pending > 0) {
    window.dispatchEvent(new CustomEvent(SERVER_WAKING_EVENT, { detail: pending > 0 }));
  }
}

/** Fire-and-forget ping so the backend is already booting while the user types. */
export function wakeBackend() {
  fetch(`${BASE_URL}/health`, { mode: "cors", cache: "no-store" }).catch(() => {});
}

/** No response at all, or the host's proxy saying the app isn't up yet: the request never reached the app. */
function isServerStarting(error: AxiosError) {
  if (!error.response) return error.code !== "ERR_CANCELED";
  return [502, 503, 504].includes(error.response.status);
}

type RetryConfig = InternalAxiosRequestConfig & { _wakeStartedAt?: number };

// Request interceptor — attach auth token from localStorage
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("verilab_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — retry while the server wakes, then surface errors consistently
apiClient.interceptors.response.use(
  (response) => {
    if ((response.config as RetryConfig)._wakeStartedAt) setWaking(-1);
    return response;
  },
  async (error: AxiosError<{ detail?: string }>) => {
    const config = error.config as RetryConfig | undefined;
    if (config && isServerStarting(error)) {
      if (!config._wakeStartedAt) {
        config._wakeStartedAt = Date.now();
        setWaking(1);
      }
      if (Date.now() - config._wakeStartedAt < MAX_WAIT_MS) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        return apiClient.request(config);
      }
    }
    if (config?._wakeStartedAt) setWaking(-1);
    const message =
      error.response?.data?.detail ?? error.message ?? "Unknown error";
    return Promise.reject(new Error(message));
  }
);

// Default export for any legacy imports that use `import api from ...`
export default apiClient;
