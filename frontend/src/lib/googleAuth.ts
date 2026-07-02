import { apiFetch } from "../api/client";

const ENV_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID ?? "";

let cachedClientId: string | null = ENV_CLIENT_ID || null;
let resolvePromise: Promise<string | null> | null = null;
let scriptPromise: Promise<void> | null = null;
let initializedClientId: string | null = null;
let credentialHandler: ((credential: string) => void) | null = null;

export function getGoogleClientId(): string {
  return cachedClientId ?? "";
}

export function isGoogleAuthConfigured(): boolean {
  return Boolean(cachedClientId);
}

interface GoogleCredentialResponse {
  credential?: string;
  select_by?: string;
}

interface GoogleIdApi {
  initialize: (config: {
    client_id: string;
    callback: (response: GoogleCredentialResponse) => void;
    auto_select?: boolean;
    cancel_on_tap_outside?: boolean;
  }) => void;
  renderButton: (
    parent: HTMLElement,
    options: {
      type?: string;
      theme?: string;
      size?: string;
      text?: string;
      locale?: string;
      width?: number;
    }
  ) => void;
  cancel: () => void;
}

declare global {
  interface Window {
    google?: {
      accounts: {
        id: GoogleIdApi;
      };
    };
  }
}

export function setGoogleCredentialHandler(handler: (credential: string) => void): void {
  credentialHandler = handler;
}

export function ensureGoogleInitialized(clientId: string): void {
  if (!window.google?.accounts?.id) {
    throw new Error("Script Google indisponible");
  }
  if (initializedClientId === clientId) {
    return;
  }
  window.google.accounts.id.initialize({
    client_id: clientId,
    callback: (response) => {
      if (response.credential) {
        credentialHandler?.(response.credential);
      }
    },
    auto_select: false,
    cancel_on_tap_outside: true,
  });
  initializedClientId = clientId;
}

export function renderGoogleButton(
  container: HTMLElement,
  options?: { width?: number }
): void {
  if (!window.google?.accounts?.id) {
    throw new Error("Script Google indisponible");
  }
  container.innerHTML = "";
  const width = Math.min(Math.max(options?.width ?? (container.offsetWidth || 360), 240), 400);
  window.google.accounts.id.renderButton(container, {
    type: "standard",
    theme: "outline",
    size: "large",
    text: "continue_with",
    locale: "fr",
    width,
  });
}

export function loadGoogleScript(): Promise<void> {
  if (window.google?.accounts?.id) {
    return Promise.resolve();
  }
  if (scriptPromise) {
    return scriptPromise;
  }

  scriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Impossible de charger l'authentification Google"));
    document.head.appendChild(script);
  });

  return scriptPromise;
}

export async function resolveGoogleClientId(): Promise<string | null> {
  if (cachedClientId) {
    return cachedClientId;
  }
  if (!resolvePromise) {
    resolvePromise = apiFetch<{ enabled: boolean; client_id?: string | null }>(
      "/auth/google/config"
    )
      .then((config) => {
        if (config.enabled && config.client_id) {
          cachedClientId = config.client_id;
          return cachedClientId;
        }
        return null;
      })
      .catch(() => null)
      .finally(() => {
        resolvePromise = null;
      });
  }
  return resolvePromise;
}
