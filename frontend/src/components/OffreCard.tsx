import { HTMLAttributes, ReactNode } from "react";
import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import type { OffreContact } from "../api/types";
import {
  formatOffreUrl,
  hasStructuredContact,
  resolveOffreContact,
  type OffreContactInfo,
} from "../lib/offreContact";

export interface OffreCardProps extends HTMLAttributes<HTMLElement> {
  offreId?: string;
  titre: string;
  organisme: string;
  dateLimite?: string;
  description?: string | null;
  contact?: OffreContact | null;
  lienSource?: string | null;
  isFavori?: boolean;
  onToggleFavori?: () => void;
  favoriLoading?: boolean;
  showDetailLink?: boolean;
}

function ContactDetail({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div className="dashboard-offre-contact-detail">
      <span className="dashboard-offre-contact-detail-label">{label}</span>
      <div className="dashboard-offre-contact-detail-value">{children}</div>
    </div>
  );
}

function ContactList({
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
    <div className="dashboard-offre-contact">
      <p className="dashboard-offre-contact-label">Contact</p>
      {organisme && (
        <p className="dashboard-offre-contact-organisme">{organisme}</p>
      )}
      {info.responsable && (
        <ContactDetail label="Responsable">{info.responsable}</ContactDetail>
      )}
      {info.emails.map((email) => (
        <a
          key={email}
          href={`mailto:${email}`}
          className="dashboard-offre-contact-item"
        >
          {email}
        </a>
      ))}
      {info.phones.map((phone) => (
        <a
          key={phone}
          href={`tel:${phone.replace(/\s/g, "")}`}
          className="dashboard-offre-contact-item"
        >
          {phone}
        </a>
      ))}
      {info.siteWeb && (
        <a
          href={info.siteWeb.startsWith("http") ? info.siteWeb : `https://${info.siteWeb}`}
          target="_blank"
          rel="noopener noreferrer"
          className="dashboard-offre-contact-item"
        >
          {info.siteWeb}
        </a>
      )}
      {info.lieuAcquisitionDao && (
        <ContactDetail label="Acquisition DAO">{info.lieuAcquisitionDao}</ContactDetail>
      )}
      {info.lieuDepot && (
        <ContactDetail label="Dépôt des offres">{info.lieuDepot}</ContactDetail>
      )}
      {info.lieuOuverturePlis && (
        <ContactDetail label="Ouverture des plis">{info.lieuOuverturePlis}</ContactDetail>
      )}
      {!hasContact && lienSource && (
        <p className="dashboard-offre-contact-hint">
          Coordonnées complètes disponibles sur le dossier de l&apos;appel
          d&apos;offres.
        </p>
      )}
      {!hasContact && !lienSource && (
        <p className="dashboard-offre-contact-hint">
          Coordonnées non publiées sur MarchéConnect.
        </p>
      )}
    </div>
  );
}

export function OffreCard({
  offreId,
  titre,
  organisme,
  dateLimite,
  description,
  contact,
  lienSource,
  isFavori = false,
  onToggleFavori,
  favoriLoading = false,
  showDetailLink = true,
  className,
  ...props
}: OffreCardProps) {
  const contactInfo = resolveOffreContact(contact, description);
  const detailHref = offreId ? `/offres/${offreId}` : undefined;

  return (
    <article
      className={cn("dashboard-offre-card group flex flex-col", className)}
      {...props}
    >
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="dashboard-offre-title min-w-0 flex-1">
          {detailHref ? (
            <Link to={detailHref} className="dashboard-offre-title-link">
              {titre}
            </Link>
          ) : (
            titre
          )}
        </h3>
        {onToggleFavori && (
          <button
            type="button"
            onClick={onToggleFavori}
            disabled={favoriLoading}
            className={cn(
              "shrink-0 rounded-lg px-2 py-1 text-xs font-semibold transition-colors",
              isFavori
                ? "bg-brand text-white"
                : "bg-neutral-100 text-neutral-600 hover:bg-brand-muted"
            )}
            aria-label={isFavori ? "Retirer des favoris" : "Ajouter aux favoris"}
          >
            {favoriLoading ? "…" : isFavori ? "★" : "☆"}
          </button>
        )}
      </div>

      {dateLimite && (
        <p className="dashboard-offre-deadline">
          <span>Date limite</span> {dateLimite}
        </p>
      )}

      <div className="dashboard-offre-actions">
        {showDetailLink && detailHref && (
          <Link
            to={detailHref}
            className="mb-3 inline-flex text-sm font-semibold text-brand hover:underline"
          >
            Voir le détail →
          </Link>
        )}

        {lienSource ? (
          <a
            href={lienSource}
            target="_blank"
            rel="noopener noreferrer"
            className="dashboard-offre-primary-link focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/30 rounded-lg"
          >
            <span className="dashboard-offre-primary-link-label">
              Accéder à l&apos;offre
            </span>
            <span className="dashboard-offre-primary-link-url">
              {formatOffreUrl(lienSource)}
            </span>
          </a>
        ) : (
          <p className="dashboard-offre-missing-link">
            Lien vers l&apos;offre non disponible
          </p>
        )}

        <ContactList
          info={contactInfo}
          organisme={organisme}
          lienSource={lienSource}
        />
      </div>
    </article>
  );
}
