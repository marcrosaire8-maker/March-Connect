import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/cn";
import { Button } from "./Button";
import { SiteBrand } from "./SiteBrand";

const navLinks = [
  { to: "/", label: "Accueil", match: (p: string) => p === "/" },
  { to: "/a-propos", label: "À propos", match: (p: string) => p === "/a-propos" },
  { to: "/contact", label: "Contact", match: (p: string) => p === "/contact" },
];

export function PublicHeader() {
  const { pathname } = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-white/40 bg-surface/80 backdrop-blur-md">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6 lg:px-8">
        <SiteBrand to="/" size="md" />

        <nav className="hidden items-center gap-1 md:flex" aria-label="Navigation publique">
          {navLinks.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              className={cn(
                "rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                link.match(pathname)
                  ? "bg-brand/10 text-brand"
                  : "text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900"
              )}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 md:flex">
          <Link to="/connexion">
            <Button variant="outline" className="min-h-10 px-4 py-2 text-sm">
              Connexion
            </Button>
          </Link>
          <Link to="/inscription">
            <Button className="min-h-10 px-4 py-2 text-sm">S&apos;inscrire</Button>
          </Link>
        </div>

        <button
          type="button"
          className="inline-flex size-10 items-center justify-center rounded-lg text-neutral-700 hover:bg-neutral-100 md:hidden"
          aria-expanded={mobileOpen}
          aria-label={mobileOpen ? "Fermer le menu" : "Ouvrir le menu"}
          onClick={() => setMobileOpen((o) => !o)}
        >
          <svg className="size-6" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" aria-hidden="true">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {mobileOpen && (
        <div className="border-t border-neutral-200/80 bg-white px-4 py-4 md:hidden">
          <nav className="space-y-1">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                onClick={() => setMobileOpen(false)}
                className={cn(
                  "block rounded-lg px-3 py-2.5 text-sm font-medium",
                  link.match(pathname) ? "bg-brand/10 text-brand" : "text-neutral-700"
                )}
              >
                {link.label}
              </Link>
            ))}
            <Link
              to="/connexion"
              onClick={() => setMobileOpen(false)}
              className="block rounded-lg px-3 py-2.5 text-sm font-medium text-neutral-700"
            >
              Connexion
            </Link>
            <Link to="/inscription" onClick={() => setMobileOpen(false)} className="mt-2 block">
              <Button fullWidth>S&apos;inscrire</Button>
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
