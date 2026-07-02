import { apiFetch } from "../api/client";

const ENV_CLIENT_ID = import.meta.env.VITE_APPLE_CLIENT_ID ?? "";

export interface AppleAuthConfig {
  clientId: string;
  redirectUri: string;
}

export interface AppleSignInResult {
  credential: string;
  prenom?: string;
  nom?: string;
}

interface AppleAuthorization {
  id_token?: string;
  code?: string;
  state?: string;
}

interface AppleUserName {
  firstName?: string;
  lastName?: string;
}

interface AppleUser {
  email?: string;
  name?: AppleUserName;
}

interface AppleSignInResponse {
  authorization?: AppleAuthorization;
  user?: AppleUser;
}

interface AppleAuthApi {
  init: (config: {
    clientId: string;
    scope?: string;
    redirectURI: string;
    state?: string;
    usePopup?: boolean;
  }) => void;
  signIn: () => Promise<AppleSignInResponse>;
}

declare global {
  interface Window {
    AppleID?: {
      auth: AppleAuthApi;
    };
  }
}

let cachedConfig: AppleAuthConfig | null = ENV_CLIENT_ID
  ? { clientId: ENV_CLIENT_ID, redirectUri: window.location.origin }
  : null;
let resolvePromise: Promise<AppleAuthConfig | null> | null = null;
let scriptPromise: Promise<void> | null = null;
let initialized = false;

export function isAppleAuthConfigured(): boolean {
  return Boolean(cachedConfig?.clientId);
}

export function loadAppleScript(): Promise<void> {
  if (window.AppleID?.auth) {
    return Promise.resolve();
  }
  if (scriptPromise) {
    return scriptPromise;
  }

  scriptPromise = new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src =
      "https://appleid.cdn-apple.com/appleauth/static/jsapi/appleid/1/en_US/appleid.auth.js";
    script.async = true;
    script.defer = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("Impossible de charger l'authentification Apple"));
    document.head.appendChild(script);
  });

  return scriptPromise;
}

export async function resolveAppleConfig(): Promise<AppleAuthConfig | null> {
  if (cachedConfig) {
    return cachedConfig;
  }
  if (!resolvePromise) {
    resolvePromise = apiFetch<{
      enabled: boolean;
      client_id?: string | null;
      redirect_uri?: string | null;
    }>("/auth/apple/config")
      .then((config) => {
        if (config.enabled && config.client_id && config.redirect_uri) {
          cachedConfig = {
            clientId: config.client_id,
            redirectUri: config.redirect_uri,
          };
          return cachedConfig;
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

function ensureAppleInitialized(config: AppleAuthConfig): void {
  if (initialized || !window.AppleID?.auth) {
    return;
  }
  window.AppleID.auth.init({
    clientId: config.clientId,
    scope: "name email",
    redirectURI: config.redirectUri,
    usePopup: true,
  });
  initialized = true;
}

export async function signInWithApple(): Promise<AppleSignInResult> {
  const config = await resolveAppleConfig();
  if (!config) {
    throw new Error("La connexion Apple n'est pas configurée");
  }

  await loadAppleScript();
  ensureAppleInitialized(config);

  if (!window.AppleID?.auth) {
    throw new Error("Script Apple indisponible");
  }

  const response = await window.AppleID.auth.signIn();
  const credential = response.authorization?.id_token;
  if (!credential) {
    throw new Error("Authentification Apple incomplète");
  }

  return {
    credential,
    prenom: response.user?.name?.firstName,
    nom: response.user?.name?.lastName,
  };
}
