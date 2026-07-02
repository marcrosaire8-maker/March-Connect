export function formatDate(value?: string | null): string {
  if (!value) return "Non précisée";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
}

export function formatDateTime(value?: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const PAYS_OPTIONS = [
  "Bénin",
  "Côte d'Ivoire",
  "Mali",
  "Sénégal",
  "Togo",
  "France",
  "Europe",
  "Afrique du Sud",
] as const;
