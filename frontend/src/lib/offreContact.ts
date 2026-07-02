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

const EMAIL_RE =
  /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
const PHONE_RE =
  /(?:\+?\d{1,4}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?){2,4}\d{2,4}/g;

function unique(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];
  for (const value of values) {
    const normalized = value.trim();
    if (!normalized || seen.has(normalized.toLowerCase())) continue;
    seen.add(normalized.toLowerCase());
    result.push(normalized);
  }
  return result;
}

function isLikelyPhone(value: string): boolean {
  const digits = value.replace(/\D/g, "");
  return digits.length >= 8 && digits.length <= 15;
}

export interface OffreContactInfo {
  email?: string;
  telephone?: string;
  telephoneResponsable?: string;
  fax?: string;
  responsable?: string;
  siteWeb?: string;
  lieuDepot?: string;
  lieuAcquisitionDao?: string;
  lieuOuverturePlis?: string;
  emails: string[];
  phones: string[];
}

function pushPhone(target: string[], value?: string | null) {
  if (!value?.trim() || !isLikelyPhone(value)) return;
  target.push(value.trim());
}

export function extractOffreContacts(
  description?: string | null,
): Pick<OffreContactInfo, "emails" | "phones"> {
  const text = description ?? "";
  const emails = unique((text.match(EMAIL_RE) ?? []).map((v) => v.toLowerCase()));
  const phones = unique(
    (text.match(PHONE_RE) ?? []).filter(isLikelyPhone),
  );
  return { emails, phones };
}

export function resolveOffreContact(
  contact?: OffreContact | null,
  description?: string | null,
): OffreContactInfo {
  const extracted = extractOffreContacts(description);
  const phones: string[] = [];

  pushPhone(phones, contact?.telephone);
  pushPhone(phones, contact?.telephone_responsable);
  pushPhone(phones, contact?.fax);
  for (const phone of extracted.phones) pushPhone(phones, phone);

  const emails = unique([
    ...(contact?.email ? [contact.email.toLowerCase()] : []),
    ...extracted.emails,
  ]);

  return {
    email: contact?.email ?? emails[0],
    telephone: contact?.telephone ?? undefined,
    telephoneResponsable: contact?.telephone_responsable ?? undefined,
    fax: contact?.fax ?? undefined,
    responsable: contact?.responsable ?? undefined,
    siteWeb: contact?.site_web ?? undefined,
    lieuDepot: contact?.lieu_depot ?? undefined,
    lieuAcquisitionDao: contact?.lieu_acquisition_dao ?? undefined,
    lieuOuverturePlis: contact?.lieu_ouverture_plis ?? undefined,
    emails,
    phones: unique(phones),
  };
}

export function formatOffreUrl(url: string): string {
  try {
    const parsed = new URL(url);
    const path = `${parsed.pathname}${parsed.search}`;
    if (path && path !== "/") {
      return `${parsed.hostname}${path}`;
    }
    return parsed.hostname;
  } catch {
    return url;
  }
}

export function hasStructuredContact(info: OffreContactInfo): boolean {
  return Boolean(
    info.emails.length ||
      info.phones.length ||
      info.responsable ||
      info.siteWeb ||
      info.lieuDepot ||
      info.lieuAcquisitionDao ||
      info.lieuOuverturePlis,
  );
}
