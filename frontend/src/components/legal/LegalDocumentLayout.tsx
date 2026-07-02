import { FileText } from "lucide-react";
import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { ContentCard } from "../design/ContentCard";
import { PageHeader } from "../design/PageHeader";
import { pageGradient } from "../../lib/design";

interface LegalDocumentLayoutProps {
  title: string;
  badge: string;
  updated?: string;
  children: ReactNode;
  backTo?: { label: string; href: string };
}

export function LegalSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <ContentCard padding="md" className="space-y-3">
      <h2 className="text-base font-semibold text-neutral-900">{title}</h2>
      <div className="space-y-2 text-sm leading-relaxed text-neutral-600">{children}</div>
    </ContentCard>
  );
}

export function LegalDocumentLayout({
  title,
  badge,
  updated = "juillet 2026",
  children,
  backTo = { label: "Retour à l'accueil", href: "/" },
}: LegalDocumentLayoutProps) {
  return (
    <div className={pageGradient}>
      <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <PageHeader
          badge={badge}
          title={title}
          subtitle={
            <span className="inline-flex items-center justify-center gap-2 text-base text-neutral-500">
              <FileText className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
              Dernière mise à jour : {updated}
            </span>
          }
        />

        <div className="space-y-4">{children}</div>

        <ContentCard padding="md" className="mt-8 flex flex-wrap items-center justify-between gap-3">
          <Link
            to={backTo.href}
            className="text-sm font-semibold text-brand transition-colors hover:underline"
          >
            ← {backTo.label}
          </Link>
          <div className="flex flex-wrap gap-4 text-sm text-neutral-500">
            <Link to="/politique-de-confidentialite" className="hover:text-brand">
              Confidentialité
            </Link>
            <Link to="/mentions-legales" className="hover:text-brand">
              Mentions légales
            </Link>
            <Link to="/conditions-utilisation" className="hover:text-brand">
              CGU
            </Link>
          </div>
        </ContentCard>
      </div>
    </div>
  );
}
