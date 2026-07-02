import { useState } from "react";
import { Link } from "react-router-dom";
import { cn } from "../lib/cn";
import { Button } from "./Button";
import { SiteBrand } from "./SiteBrand";

export interface NavbarUser {
  email: string;
  role: "client" | "admin";
}

export interface NavbarProps {
  user?: NavbarUser | null;
  onLogout?: () => void;
}

function MenuIcon({ open }: { open: boolean }) {
  return (
    <svg
      className="size-6"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={2}
      stroke="currentColor"
      aria-hidden="true"
    >
      {open ? (
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      ) : (
        <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
      )}
    </svg>
  );
}

export function Navbar({ user = null, onLogout }: NavbarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const isGuest = !user;
  const isAdmin = user?.role === "admin";

  const navLinks = isAdmin
    ? [{ to: "/admin", label: "Administration" }]
    : [
        { to: "/offres", label: "Offres" },
        { to: "/mon-compte", label: "Mon compte" },
      ];

  const homeLink = isGuest ? "/connexion" : isAdmin ? "/admin" : "/offres";

  return (
    <header className="sticky top-0 z-50 border-b border-primary-dark/20 bg-primary-dark text-primary-foreground">
      <nav
        className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8"
        aria-label="Navigation principale"
      >
        <SiteBrand to={homeLink} size="md" variant="light" className="rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent focus-visible:ring-offset-2 focus-visible:ring-offset-primary-dark" />

        <div className="hidden items-center gap-6 md:flex">
          <ul className="flex items-center gap-1">
            {navLinks.map((link) => (
              <li key={link.to}>
                <Link
                  to={link.to}
                  className="rounded-lg px-3 py-2 text-body-sm font-medium text-neutral-200 transition-colors hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                >
                  {link.label}
                </Link>
              </li>
            ))}
          </ul>

          <div className="flex items-center gap-3 border-l border-white/20 pl-6">
            {isGuest ? (
              <>
                <Link to="/connexion">
                  <Button
                    variant="outline"
                    className="border-white/40 text-white hover:bg-white hover:text-primary-dark"
                  >
                    Connexion
                  </Button>
                </Link>
                <Link to="/inscription">
                  <Button variant="accent">Créer un compte</Button>
                </Link>
              </>
            ) : (
              <>
                <span
                  className="max-w-[160px] truncate text-body-sm text-neutral-300"
                  title={user.email}
                >
                  {user.email}
                </span>
                <button
                  type="button"
                  onClick={onLogout}
                  className="rounded-lg px-3 py-2 text-body-sm text-neutral-300 transition-colors hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
                >
                  Déconnexion
                </button>
              </>
            )}
          </div>
        </div>

        <button
          type="button"
          className="rounded-lg p-2 text-white md:hidden focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-expanded={mobileOpen}
          aria-controls="mobile-menu"
          aria-label={mobileOpen ? "Fermer le menu" : "Ouvrir le menu"}
        >
          <MenuIcon open={mobileOpen} />
        </button>
      </nav>

      <div
        id="mobile-menu"
        className={cn(
          "border-t border-white/10 bg-primary-dark md:hidden",
          mobileOpen ? "block" : "hidden"
        )}
      >
        <ul className="space-y-1 px-4 py-3">
          {navLinks.map((link) => (
            <li key={link.to}>
              <Link
                to={link.to}
                className="block rounded-lg px-3 py-2.5 text-body font-medium text-neutral-200 hover:bg-white/10"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            </li>
          ))}
        </ul>
        <div className="space-y-2 border-t border-white/10 px-4 py-4">
          {isGuest ? (
            <>
              <Link to="/connexion" className="block" onClick={() => setMobileOpen(false)}>
                <Button
                  variant="outline"
                  fullWidth
                  className="border-white/40 text-white hover:bg-white hover:text-primary-dark"
                >
                  Connexion
                </Button>
              </Link>
              <Link to="/inscription" className="block" onClick={() => setMobileOpen(false)}>
                <Button variant="accent" fullWidth>
                  Créer un compte
                </Button>
              </Link>
            </>
          ) : (
            <>
              <p className="truncate px-1 text-body-sm text-neutral-400">{user.email}</p>
              <Button variant="secondary" fullWidth onClick={onLogout}>
                Déconnexion
              </Button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
