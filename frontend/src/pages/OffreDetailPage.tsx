import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Building2,
  CalendarClock,
  ExternalLink,
  FileText,
  Heart,
  Mail,
  MapPin,
  Phone,
  Share2,
  User,
} from "lucide-react";
import { Button, LoadingState } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { favorisApi, offresApi, secteursApi } from "../api";
import type { Offre } from "../api/types";
import { cn } from "../lib/cn";
import { formatDate } from "../lib/format";
import {
  formatOffreUrl,
  hasStructuredContact,
  resolveOffreContact,
  type OffreContactInfo,
} from "../lib/offreContact";
import { getSecteurIcon } from "../lib/secteurVisual";

type DeadlineUrgency = "expired" | "urgent" | "normal" | "none";

function getDeadlineUrgency(dateLimite?: string | null): DeadlineUrgency {
  if (!dateLimite) return "none";
  const deadline = new Date(dateLimite);
  if (Number.isNaN(deadline.getTime())) return "none";
  const days = (deadline.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
  if (days < 0) return "expired";
  if (days <= 7) return "urgent";
  return "normal";
}

const deadlineStyles: Record<
  Exclude<DeadlineUrgency, "none">,
  string
> = {
  urgent: "border-amber-200 bg-amber-50 text-amber-800",
  normal: "border-brand/20 bg-brand-muted text-brand-dark",
  expired: "border-neutral-200 bg-neutral-100 text-neutral-600",
};

function truncateDisplayUrl(url: string, maxLength = 52): string {
  const formatted = formatOffreUrl(url);
  if (formatted.length <= maxLength) return formatted;
  return `${formatted.slice(0, maxLength)}…`;
}

function DetailCard({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn(
        "rounded-2xl border border-neutral-100 bg-white p-5 shadow-sm sm:p-6",
        className
      )}
    >
      {children}
    </section>
  );
}

function ContactRow({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof Building2;
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="flex gap-3 border-t border-neutral-100 pt-4 first:border-t-0 first:pt-0">
      <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand-muted">
        <Icon className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[0.6875rem] font-semibold uppercase tracking-wide text-neutral-500">
          {label}
        </p>
        <div className="mt-1 text-sm text-neutral-800">{children}</div>
      </div>
    </div>
  );
}

function ContactSection({
  info,
  organisme,
  lienSource,
}: {
  info: OffreContactInfo;
  organisme: string;
  lienSource?: string | null;
}) {
  const hasContact = hasStructuredContact(info);

  return (
    <DetailCard>
      <h2 className="mb-5 text-sm font-semibold uppercase tracking-wide text-neutral-800">
        Contact
      </h2>
      <div className="space-y-0">
        {organisme && (
          <ContactRow icon={Building2} label="Organisme">
            {organisme}
          </ContactRow>
        )}
        {info.responsable && (
          <ContactRow icon={User} label="Responsable">
            {info.responsable}
          </ContactRow>
        )}
        {info.emails.map((email) => (
          <ContactRow key={email} icon={Mail} label="E-mail">
            <a href={`mailto:${email}`} className="text-brand hover:underline break-all">
              {email}
            </a>
          </ContactRow>
        ))}
        {info.phones.map((phone) => (
          <ContactRow key={phone} icon={Phone} label="Téléphone">
            <a
              href={`tel:${phone.replace(/\s/g, "")}`}
              className="inline-flex items-center gap-1.5 text-brand hover:underline"
            >
              <Phone className="size-3.5" strokeWidth={2} aria-hidden="true" />
              {phone}
            </a>
          </ContactRow>
        ))}
        {info.lieuAcquisitionDao && (
          <ContactRow icon={MapPin} label="Acquisition DAO">
            {info.lieuAcquisitionDao}
          </ContactRow>
        )}
        {info.lieuDepot && (
          <ContactRow icon={MapPin} label="Dépôt des offres">
            {info.lieuDepot}
          </ContactRow>
        )}
        {info.lieuOuverturePlis && (
          <ContactRow icon={MapPin} label="Ouverture des plis">
            {info.lieuOuverturePlis}
          </ContactRow>
        )}
        {!hasContact && lienSource && (
          <p className="text-sm text-neutral-500">
            Coordonnées complètes disponibles sur le dossier de l&apos;appel d&apos;offres.
          </p>
        )}
        {!hasContact && !lienSource && (
          <p className="text-sm text-neutral-500">
            Coordonnées non publiées sur MarchéConnect.
          </p>
        )}
      </div>
    </DetailCard>
  );
}

export function OffreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [offre, setOffre] = useState<Offre | null>(null);
  const [secteurNom, setSecteurNom] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFavori, setIsFavori] = useState(false);
  const [favLoading, setFavLoading] = useState(false);
  const [shareHint, setShareHint] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, favoris, secteurs] = await Promise.all([
        offresApi.get(id),
        favorisApi.list(),
        secteursApi.list(),
      ]);
      setOffre(detail);
      setIsFavori(favoris.includes(id));
      if (detail.secteur_id) {
        setSecteurNom(secteurs.find((s) => s.id === detail.secteur_id)?.nom ?? null);
      } else {
        setSecteurNom(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Offre introuvable");
      setOffre(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleFavori = async () => {
    if (!offre) return;
    setFavLoading(true);
    try {
      if (isFavori) {
        await favorisApi.remove(offre.id);
        setIsFavori(false);
      } else {
        await favorisApi.add(offre.id);
        setIsFavori(true);
      }
    } finally {
      setFavLoading(false);
    }
  };

  const handleShare = async () => {
    if (!offre) return;
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title: offre.titre, url });
      } else {
        await navigator.clipboard.writeText(url);
        setShareHint("Lien copié dans le presse-papiers");
        window.setTimeout(() => setShareHint(null), 2500);
      }
    } catch {
      /* annulation du partage */
    }
  };

  const deadlineUrgency = useMemo(
    () => (offre ? getDeadlineUrgency(offre.date_limite) : "none"),
    [offre]
  );

  const descriptionIsRedundant = useMemo(() => {
    if (!offre?.description) return true;
    return offre.description.trim() === offre.titre.trim();
  }, [offre]);

  if (loading) {
    return (
      <div className="min-h-0 flex-1 bg-gradient-to-b from-white via-surface to-brand-muted/40">
        <DashboardPage title="Détail de l'offre" badge="Chargement…">
          <LoadingState variant="spinner" />
        </DashboardPage>
      </div>
    );
  }

  if (error || !offre) {
    return (
      <div className="min-h-0 flex-1 bg-gradient-to-b from-white via-surface to-brand-muted/40">
        <DashboardPage title="Offre introuvable">
          <p className="text-sm text-danger">{error ?? "Cette offre n'existe pas."}</p>
          <Button variant="secondary" className="mt-4" onClick={() => navigate("/offres")}>
            Retour aux offres
          </Button>
        </DashboardPage>
      </div>
    );
  }

  const contactInfo = resolveOffreContact(offre.contact, offre.description);
  const SecteurIcon = getSecteurIcon(secteurNom);
  const formattedDeadline = offre.date_limite ? formatDate(offre.date_limite) : null;

  return (
    <div className="min-h-0 flex-1 bg-gradient-to-b from-white via-surface to-brand-muted/40">
      <DashboardPage
        title="Détail de l'offre"
        badge="Offre active"
        subtitle={
          <>
            <MapPin className="size-4 shrink-0 text-brand" strokeWidth={2} aria-hidden="true" />
            <span>
              {offre.organisme} · {offre.pays}
            </span>
          </>
        }
      >
        <div className="mx-auto max-w-4xl space-y-6">
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            <Link
              to="/offres"
              className="inline-flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm font-medium text-brand transition-colors hover:bg-brand-muted hover:underline"
            >
              <ArrowLeft className="size-4" strokeWidth={2} aria-hidden="true" />
              Retour aux offres
            </Link>

            <div className="ml-auto flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => void toggleFavori()}
                disabled={favLoading}
                className={cn(
                  "inline-flex min-h-10 items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-all duration-200",
                  isFavori
                    ? "border-brand bg-brand text-white shadow-sm shadow-brand/20"
                    : "border-neutral-200 bg-white text-neutral-700 hover:border-brand/30 hover:bg-brand-muted hover:text-brand-dark"
                )}
              >
                <Heart
                  className={cn("size-4", isFavori && "fill-current")}
                  strokeWidth={2}
                  aria-hidden="true"
                />
                {favLoading
                  ? "…"
                  : isFavori
                    ? "Dans les favoris"
                    : "Ajouter aux favoris"}
              </button>

              <button
                type="button"
                onClick={() => void handleShare()}
                className="inline-flex min-h-10 items-center gap-2 rounded-full border border-neutral-200 bg-white px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:border-brand/30 hover:bg-brand-muted hover:text-brand-dark"
              >
                <Share2 className="size-4" strokeWidth={2} aria-hidden="true" />
                Partager
              </button>
            </div>
          </div>

          {shareHint && (
            <p className="text-center text-xs font-medium text-brand" role="status">
              {shareHint}
            </p>
          )}

          <DetailCard className="border-l-4 border-l-brand shadow-md">
            {secteurNom && (
              <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand/20 bg-brand-muted px-3 py-1 text-xs font-semibold text-brand-dark">
                <SecteurIcon className="size-3.5" strokeWidth={2} aria-hidden="true" />
                {secteurNom}
              </span>
            )}

            <h2 className="text-xl font-bold leading-snug text-neutral-900 sm:text-2xl">
              {offre.titre}
            </h2>

            {formattedDeadline && deadlineUrgency !== "none" && (
              <div className="mt-4">
                <span
                  className={cn(
                    "inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm font-semibold",
                    deadlineStyles[deadlineUrgency]
                  )}
                >
                  <CalendarClock className="size-4" strokeWidth={2} aria-hidden="true" />
                  Date limite {formattedDeadline}
                  {deadlineUrgency === "urgent" && (
                    <span className="text-[0.6875rem] font-bold uppercase tracking-wide">
                      · Bientôt
                    </span>
                  )}
                  {deadlineUrgency === "expired" && (
                    <span className="text-[0.6875rem] font-bold uppercase tracking-wide">
                      · Expirée
                    </span>
                  )}
                </span>
              </div>
            )}
          </DetailCard>

          {offre.lien_source ? (
            <DetailCard>
              <div className="flex flex-wrap items-start gap-3">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-muted">
                  <ExternalLink className="size-5 text-brand" strokeWidth={2} aria-hidden="true" />
                </div>
                <div className="min-w-0 flex-1">
                  <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-800">
                    Accéder à l&apos;offre
                  </h2>
                  <a
                    href={offre.lien_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-2 block truncate text-sm text-brand hover:underline"
                    title={formatOffreUrl(offre.lien_source)}
                  >
                    {truncateDisplayUrl(offre.lien_source)}
                  </a>
                  <a
                    href={offre.lien_source}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-4 inline-flex items-center gap-2 rounded-full bg-brand px-5 py-2.5 text-sm font-semibold text-white shadow-md shadow-brand/20 transition-all hover:bg-brand-dark hover:shadow-lg hover:shadow-brand/25"
                  >
                    Voir l&apos;offre officielle
                    <ExternalLink className="size-4" strokeWidth={2} aria-hidden="true" />
                  </a>
                </div>
              </div>
            </DetailCard>
          ) : (
            <DetailCard>
              <p className="text-sm text-neutral-500">Lien vers l&apos;offre non disponible.</p>
            </DetailCard>
          )}

          <ContactSection
            info={contactInfo}
            organisme={offre.organisme}
            lienSource={offre.lien_source}
          />

          {offre.description && !descriptionIsRedundant && (
            <DetailCard>
              <div className="mb-4 flex items-center gap-2.5 border-b border-neutral-100 pb-4">
                <div className="flex size-9 items-center justify-center rounded-full bg-brand-muted">
                  <FileText className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                </div>
                <h2 className="text-sm font-semibold uppercase tracking-wide text-neutral-800">
                  Description
                </h2>
              </div>
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
                {offre.description}
              </p>
            </DetailCard>
          )}

          {offre.montant_estime && (
            <DetailCard>
              <p className="text-sm text-neutral-700">
                <span className="font-semibold text-neutral-900">Montant estimé :</span>{" "}
                {offre.montant_estime}
              </p>
            </DetailCard>
          )}
        </div>
      </DashboardPage>
    </div>
  );
}
