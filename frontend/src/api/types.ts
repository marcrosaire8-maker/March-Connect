export interface Offre {
  id: string;
  source_id?: string | null;
  secteur_id?: string | null;
  titre: string;
  organisme: string;
  pays: string;
  description?: string | null;
  date_publication?: string | null;
  date_limite?: string | null;
  montant_estime?: string | null;
  lien_source?: string | null;
  contact?: OffreContact | null;
  acces_complet: boolean;
}

export interface OffreContact {
  email?: string | null;
  telephone?: string | null;
  telephone_responsable?: string | null;
  fax?: string | null;
  responsable?: string | null;
  site_web?: string | null;
  lieu_depot?: string | null;
  lieu_acquisition_dao?: string | null;
  lieu_ouverture_plis?: string | null;
}

export interface PaginatedOffres {
  items: Offre[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface Secteur {
  id: string;
  nom: string;
  mots_cles: string[];
  nb_offres_actives: number;
}

export interface Source {
  id: string;
  nom: string;
  pays: string;
  url_base: string;
  type_scraping: string;
  actif: boolean;
  config?: Record<string, unknown>;
  derniere_execution?: string | null;
}

export interface SourceCreatePayload {
  nom: string;
  pays: string;
  url_base: string;
  type_scraping: "html" | "api" | "rss";
  actif?: boolean;
  config?: Record<string, unknown>;
}

export interface User {
  id: string;
  email: string;
  role: "client" | "admin";
  date_inscription: string;
  must_change_password?: boolean;
  preferences_configurees?: boolean;
  prenom?: string | null;
  nom?: string | null;
  photo_profil?: string | null;
  auth_provider?: string | null;
  email_verifie?: boolean;
  statut_email?: string | null;
  date_verification_email?: string | null;
}

export interface RegisterResponse {
  status: "verification_required";
  email: string;
  message: string;
}

export interface GoogleAuthResponse {
  status: "authenticated" | "link_required";
  access_token?: string | null;
  token_type?: string;
  link_token?: string | null;
  email?: string | null;
  message?: string | null;
}

export type AppleAuthResponse = GoogleAuthResponse;

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface Abonne {
  id: string;
  email: string;
  emails_supplementaires: string[];
  utilisateur_id?: string | null;
  secteurs_suivis: string[];
  pays_suivis: string[];
  mots_cles_alertes: string[];
  preferences_configurees: boolean;
  actif: boolean;
  date_inscription: string;
}

export interface LogScraping {
  id: string;
  source_id: string;
  date_execution: string;
  statut: "succes" | "echec" | "partiel";
  nb_offres_trouvees: number;
  nb_offres_nouvelles: number;
  message_erreur?: string | null;
}

export interface LogNotification {
  id: string;
  date_execution: string;
  statut: "succes" | "echec" | "partiel";
  nb_emails_envoyes: number;
  nb_echecs: number;
  message_erreur?: string | null;
}

export interface AdminUtilisateur {
  id: string;
  email: string;
  role: "client" | "admin";
  date_inscription: string;
}

export interface SuiviSite {
  id: string;
  nom: string;
  url_base: string;
  actif: boolean;
  derniere_execution?: string | null;
  dernier_statut?: "succes" | "echec" | "partiel" | null;
  nb_offres_trouvees?: number | null;
  nb_offres_nouvelles?: number | null;
  message_erreur?: string | null;
  date_creation?: string | null;
}

export interface OffresFilters {
  page?: number;
  page_size?: number;
  secteur_id?: string;
  pays?: string;
  date_limite_apres?: string;
  q?: string;
  favoris_only?: boolean;
  mes_sites_only?: boolean;
}

export interface CalendrierOffreItem {
  id: string;
  titre: string;
  organisme: string;
  pays: string;
  date_limite: string;
}

export interface CalendrierJour {
  date: string;
  offres: CalendrierOffreItem[];
}

export interface CalendrierOffres {
  year: number;
  month: number;
  jours: CalendrierJour[];
  total: number;
}

export interface NotificationPreviewResult {
  statut: string;
  nb_emails_envoyes: number;
  nb_offres: number;
  message_erreur?: string | null;
}
