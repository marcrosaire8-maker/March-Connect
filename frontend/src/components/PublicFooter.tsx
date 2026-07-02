import { Link } from "react-router-dom";
import { Globe, Mail, type LucideIcon } from "lucide-react";
import { CONTACT_EMAIL, SITE_NAME, SITE_TAGLINE } from "../lib/branding";
import { SiteBrand } from "./SiteBrand";

function IconLinkedIn({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 114.126 0 2.063 2.063 0 01-2.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  );
}

function IconX({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

const legalLinks = [
  { to: "/conditions-utilisation", label: "Conditions d'utilisation" },
  { to: "/politique-de-confidentialite", label: "Politique de confidentialité" },
  { to: "/mentions-legales", label: "Mentions légales" },
  { to: "/desabonnement", label: "Désabonnement alertes" },
];

const navLinks = [
  { to: "/", label: "Accueil" },
  { to: "/a-propos", label: "À propos" },
  { to: "/contact", label: "Contact" },
  { to: "/connexion", label: "Connexion" },
];

const socialLinks: {
  href: string;
  label: string;
  Icon: LucideIcon | typeof IconLinkedIn;
  external: boolean;
}[] = [
  {
    href: "https://www.linkedin.com",
    label: "LinkedIn",
    Icon: IconLinkedIn,
    external: true,
  },
  {
    href: "https://twitter.com",
    label: "X (Twitter)",
    Icon: IconX,
    external: true,
  },
  {
    href: `mailto:${CONTACT_EMAIL}`,
    label: "E-mail",
    Icon: Mail,
    external: false,
  },
];

const footerLinkClass =
  "text-sm text-neutral-400 transition-colors duration-200 hover:text-brand-light";

export function PublicFooter() {
  return (
    <footer className="w-full border-t border-white/10 bg-gradient-to-b from-brand-950 to-brand-900 text-neutral-300">
      <div className="mx-auto w-full max-w-7xl px-6 py-12 md:px-12 md:py-16">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-4">
          {/* Colonne 1 — Marque */}
          <div className="space-y-3">
            <SiteBrand to="/" size="md" variant="light" />
            <p className="text-sm leading-relaxed text-neutral-400">{SITE_TAGLINE}</p>
            <div className="flex flex-wrap gap-2">
              {socialLinks.map(({ href, label, Icon, external }) => (
                <a
                  key={label}
                  href={href}
                  {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
                  aria-label={label}
                  className="inline-flex size-9 items-center justify-center rounded-full border border-white/10 bg-white/5 text-brand-light transition-colors hover:border-brand-light/40 hover:bg-brand/20 hover:text-white"
                >
                  <Icon className="size-4" strokeWidth={2} aria-hidden="true" />
                </a>
              ))}
            </div>
          </div>

          {/* Colonne 2 — Navigation */}
          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-light">
              Navigation
            </p>
            <ul className="space-y-2">
              {navLinks.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className={footerLinkClass}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Colonne 3 — Légal */}
          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-light">
              Informations légales
            </p>
            <ul className="space-y-2">
              {legalLinks.map((link) => (
                <li key={link.to}>
                  <Link to={link.to} className={footerLinkClass}>
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Colonne 4 — Contact */}
          <div>
            <p className="mb-3 text-sm font-semibold uppercase tracking-wide text-brand-light">
              Contact
            </p>
            <ul className="space-y-2">
              <li>
                <a href={`mailto:${CONTACT_EMAIL}`} className={`${footerLinkClass} break-all`}>
                  {CONTACT_EMAIL}
                </a>
              </li>
              <li className="flex items-start gap-2 text-sm text-neutral-400">
                <Globe className="mt-0.5 size-4 shrink-0 text-brand-light" strokeWidth={2} aria-hidden="true" />
                <span>Afrique de l&apos;Ouest — veille marchés publics régionaux</span>
              </li>
              <li>
                <Link to="/contact" className={footerLinkClass}>
                  Formulaire de contact →
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-white/10 pt-5 text-center text-xs text-neutral-500">
          © {new Date().getFullYear()} {SITE_NAME}. Tous droits réservés.
        </div>
      </div>
    </footer>
  );
}
