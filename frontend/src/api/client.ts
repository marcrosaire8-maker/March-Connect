const TOKEN_KEY = "mpo_access_token";
const PREFS_CONFIGURED_KEY = "mpo_prefs_configured";
const PREFS_EMAIL_PREFIX = "mpo_prefs_email:";

function prefsKeyForEmail(email: string): string {
  return `${PREFS_EMAIL_PREFIX}${email.trim().toLowerCase()}`;
}

export function getToken(): string | null {
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: string): void {
  sessionStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(PREFS_CONFIGURED_KEY);
}

export function markPrefsConfiguredInSession(): void {
  try {
    sessionStorage.setItem(PREFS_CONFIGURED_KEY, "1");
  } catch {
    /* ignore */
  }
}

export function markPrefsConfiguredForEmail(email: string): void {
  try {
    localStorage.setItem(prefsKeyForEmail(email), "1");
    markPrefsConfiguredInSession();
  } catch {
    /* ignore */
  }
}

export function hasPrefsConfiguredForEmail(email: string | undefined | null): boolean {
  if (!email) return false;
  try {
    return localStorage.getItem(prefsKeyForEmail(email)) === "1";
  } catch {
    return false;
  }
}

export function clearPrefsConfiguredForEmail(email: string): void {
  try {
    localStorage.removeItem(prefsKeyForEmail(email));
  } catch {
    /* ignore */
  }
}

export function hasPrefsConfiguredInSession(): boolean {
  try {
    return sessionStorage.getItem(PREFS_CONFIGURED_KEY) === "1";
  } catch {
    return false;
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const API_BASE = import.meta.env.VITE_API_URL ?? "/api";

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  authenticated = false
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  if (authenticated) {
    const token = getToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = body.detail ?? body.message ?? "";
      if (Array.isArray(detail)) {
        detail = detail.map((d: { msg?: string }) => d.msg).join(", ");
      }
    } catch {
      detail = response.statusText;
    }
    throw new ApiError(detail || `Erreur ${response.status}`, response.status, detail);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
