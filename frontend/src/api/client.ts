// ============================================================
// CrediShield AI – Axios HTTP Client
// Handles auth headers and 401 redirect automatically
// ============================================================

import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios';

const TOKEN_KEY = 'credishield_token';

/** Retrieve the stored JWT from localStorage */
export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/** Persist a JWT token in localStorage */
export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/** Remove the JWT from localStorage */
export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// Support VITE_API_URL and dynamic Render hostname resolution
function getBaseUrl(): string {
  const envUrl = (import.meta.env.VITE_API_URL as string | undefined)?.trim();

  if (envUrl && envUrl !== 'credishield-api') {
    const withProtocol = envUrl.startsWith('http://') || envUrl.startsWith('https://')
      ? envUrl
      : `https://${envUrl}`;
    return `${withProtocol.replace(/\/+$/, '')}/api`;
  }

  // Automatic fallback when hosted on Render
  if (typeof window !== 'undefined' && window.location.hostname.includes('onrender.com')) {
    return 'https://credishield-api.onrender.com/api';
  }

  // Local development proxy fallback
  return '/api';
}

const apiBase = getBaseUrl();

/** Shared Axios instance pre-configured for the CrediShield API */
const apiClient: AxiosInstance = axios.create({
  baseURL: apiBase,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30_000,
});

// ---- Request Interceptor: inject Bearer token ---- //
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = getStoredToken();
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error),
);

// ---- Response Interceptor: handle 401 globally ---- //
apiClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearStoredToken();
      // Redirect to login unless already there
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export default apiClient;

/** Typed GET helper */
export async function apiGet<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.get<T>(url, config);
  return response.data;
}

/** Typed POST helper */
export async function apiPost<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.post<T>(url, data, config);
  return response.data;
}

/** Typed PUT helper */
export async function apiPut<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.put<T>(url, data, config);
  return response.data;
}

/** Typed PATCH helper */
export async function apiPatch<T, D = unknown>(url: string, data?: D, config?: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.patch<T>(url, data, config);
  return response.data;
}
