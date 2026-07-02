import { apiFetch } from "./client";
import type {
  Abonne,
  AdminUtilisateur,
  AppleAuthResponse,
  CalendrierOffres,
  GoogleAuthResponse,
  LogNotification,
  LogScraping,
  NotificationPreviewResult,
  Offre,
  OffresFilters,
  PaginatedOffres,
  Secteur,
  Source,
  SourceCreatePayload,
  SuiviSite,
  TokenResponse,
  RegisterResponse,
  User,
} from "./types";

export const authApi = {
  register: (
    email: string,
    password: string,
    options?: { prenom?: string; nom?: string }
  ) =>
    apiFetch<RegisterResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        prenom: options?.prenom,
        nom: options?.nom,
      }),
    }),

  login: (email: string, password: string) =>
    apiFetch<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  googleAuth: (credential: string) =>
    apiFetch<GoogleAuthResponse>("/auth/google", {
      method: "POST",
      body: JSON.stringify({ credential }),
    }),

  googleLink: (link_token: string, password: string) =>
    apiFetch<TokenResponse>("/auth/google/link", {
      method: "POST",
      body: JSON.stringify({ link_token, password }),
    }),

  appleAuth: (
    credential: string,
    options?: { prenom?: string; nom?: string }
  ) =>
    apiFetch<AppleAuthResponse>("/auth/apple", {
      method: "POST",
      body: JSON.stringify({
        credential,
        prenom: options?.prenom,
        nom: options?.nom,
      }),
    }),

  appleLink: (link_token: string, password: string) =>
    apiFetch<TokenResponse>("/auth/apple/link", {
      method: "POST",
      body: JSON.stringify({ link_token, password }),
    }),

  me: () => apiFetch<User>("/auth/me", {}, true),

  forgotPassword: (email: string) =>
    apiFetch<{ message: string }>("/auth/forgot-password", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  verifyResetOtp: (email: string, code: string) =>
    apiFetch<{ reset_token: string; message: string }>("/auth/verify-reset-otp", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),

  resendResetOtp: (email: string) =>
    apiFetch<{ message: string }>("/auth/resend-reset-otp", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  verifyEmail: (email: string, code: string) =>
    apiFetch<TokenResponse>("/auth/verify-email", {
      method: "POST",
      body: JSON.stringify({ email, code }),
    }),

  resendEmailVerification: (email: string) =>
    apiFetch<{ message: string }>("/auth/resend-email-verification", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  resetPassword: (token: string, password: string, confirm_password: string) =>
    apiFetch<{ message: string }>("/auth/reset-password", {
      method: "POST",
      body: JSON.stringify({ token, password, confirm_password }),
    }),

  changePassword: (new_password: string, confirm_password: string) =>
    apiFetch<{ message: string }>(
      "/auth/change-password",
      {
        method: "POST",
        body: JSON.stringify({ new_password, confirm_password }),
      },
      true
    ),

  deleteAccount: (password: string) =>
    apiFetch<void>(
      "/auth/me",
      { method: "DELETE", body: JSON.stringify({ password }) },
      true
    ),
};

export const offresApi = {
  list: (filters: OffresFilters = {}) => {
    const params = new URLSearchParams();
    if (filters.page) params.set("page", String(filters.page));
    if (filters.page_size) params.set("page_size", String(filters.page_size));
    if (filters.secteur_id) params.set("secteur_id", filters.secteur_id);
    if (filters.pays) params.set("pays", filters.pays);
    if (filters.date_limite_apres) {
      params.set("date_limite_apres", filters.date_limite_apres);
    }
    if (filters.q) params.set("q", filters.q);
    if (filters.favoris_only) params.set("favoris_only", "true");
    if (filters.mes_sites_only) params.set("mes_sites_only", "true");
    const qs = params.toString();
    return apiFetch<PaginatedOffres>(`/offres${qs ? `?${qs}` : ""}`, {}, true);
  },

  get: (id: string) => apiFetch<Offre>(`/offres/${id}`, {}, true),

  calendrier: (year: number, month: number) =>
    apiFetch<CalendrierOffres>(
      `/offres/calendrier?year=${year}&month=${month}`,
      {},
      true
    ),
};

export const secteursApi = {
  list: (filters: Omit<OffresFilters, "page" | "page_size" | "secteur_id"> = {}) => {
    const params = new URLSearchParams();
    if (filters.pays) params.set("pays", filters.pays);
    if (filters.date_limite_apres) {
      params.set("date_limite_apres", filters.date_limite_apres);
    }
    if (filters.q) params.set("q", filters.q);
    if (filters.favoris_only) params.set("favoris_only", "true");
    if (filters.mes_sites_only) params.set("mes_sites_only", "true");
    const qs = params.toString();
    return apiFetch<Secteur[]>(`/secteurs${qs ? `?${qs}` : ""}`, {}, true);
  },
};

export const abonnesApi = {
  me: () => apiFetch<Abonne | null>("/abonnes/me", {}, true),

  save: (
    secteurs_suivis: string[],
    pays_suivis: string[],
    options?: { onboarding?: boolean; mots_cles_alertes?: string[] }
  ) =>
    apiFetch<Abonne>(
      "/abonnes",
      {
        method: "POST",
        body: JSON.stringify({
          secteurs_suivis,
          pays_suivis,
          mots_cles_alertes: options?.mots_cles_alertes ?? [],
          onboarding: options?.onboarding ?? false,
        }),
      },
      true
    ),

  addEmail: (email: string) =>
    apiFetch<Abonne>(
      "/abonnes/emails",
      { method: "POST", body: JSON.stringify({ email }) },
      true
    ),

  removeEmail: (email: string) =>
    apiFetch<Abonne>(
      `/abonnes/emails?email=${encodeURIComponent(email)}`,
      { method: "DELETE" },
      true
    ),

  unsubscribe: (abonneId: string) =>
    apiFetch<void>(`/abonnes/${abonneId}`, { method: "DELETE" }, true),

  unsubscribeByEmail: (email: string) =>
    apiFetch<{ message: string }>("/abonnes/unsubscribe", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),
};

export const suivisSitesApi = {
  list: () => apiFetch<SuiviSite[]>("/suivis-sites", {}, true),

  add: (url: string, pays?: string) =>
    apiFetch<SuiviSite>(
      "/suivis-sites",
      { method: "POST", body: JSON.stringify({ url, pays }) },
      true
    ),

  refresh: (siteId: string) =>
    apiFetch<{ statut: string; message?: string }>(
      `/suivis-sites/${siteId}/scraping`,
      { method: "POST" },
      true
    ),

  remove: (siteId: string) =>
    apiFetch<void>(`/suivis-sites/${siteId}`, { method: "DELETE" }, true),
};

export const favorisApi = {
  list: () => apiFetch<string[]>("/favoris", {}, true),

  add: (offreId: string) =>
    apiFetch<{ offre_id: string; statut: string }>(`/favoris/${offreId}`, { method: "POST" }, true),

  remove: (offreId: string) =>
    apiFetch<void>(`/favoris/${offreId}`, { method: "DELETE" }, true),
};

export const notificationsApi = {
  previewMe: () =>
    apiFetch<NotificationPreviewResult>("/notifications/preview-me", { method: "POST" }, true),
};

export const adminApi = {
  sources: () => apiFetch<Source[]>("/sources", {}, true),

  createSource: (payload: SourceCreatePayload) =>
    apiFetch<Source>(
      "/sources",
      { method: "POST", body: JSON.stringify(payload) },
      true
    ),

  logsScraping: (limit = 50) =>
    apiFetch<LogScraping[]>(`/logs?limit=${limit}`, {}, true),

  logsNotifications: (limit = 50) =>
    apiFetch<LogNotification[]>(`/logs/notifications?limit=${limit}`, {}, true),

  utilisateurs: () =>
    apiFetch<AdminUtilisateur[]>("/admin/utilisateurs", {}, true),

  deleteUtilisateur: (userId: string) =>
    apiFetch<void>(`/admin/utilisateurs/${userId}`, { method: "DELETE" }, true),

  triggerScraping: (source_id: string) =>
    apiFetch<{ statut: string; nb_offres_nouvelles: number; message_erreur?: string }>(
      "/scraping/trigger",
      { method: "POST", body: JSON.stringify({ source_id }) },
      true
    ),
};
