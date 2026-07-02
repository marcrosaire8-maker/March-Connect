import { Link } from "react-router-dom";
import { Home, LogIn, Search } from "lucide-react";
import { Button } from "../components/Button";
import { PublicFooter } from "../components/PublicFooter";
import { PublicHeader } from "../components/PublicHeader";
import { pageBadge, pageGradient, pageTitle } from "../lib/design";

export function NotFoundPage() {
  return (
    <div className={`${pageGradient} flex min-h-dvh min-h-screen flex-col`}>
      <PublicHeader />
      <main className="flex flex-1 flex-col items-center justify-center px-4 py-16">
        <div className="mx-auto max-w-lg text-center">
          <div className="mx-auto mb-6 flex size-20 items-center justify-center rounded-full bg-brand-muted">
            <Search className="size-9 text-brand" strokeWidth={1.75} aria-hidden="true" />
          </div>
          <p className={pageBadge}>Erreur 404</p>
          <h1 className={`${pageTitle} mt-4`}>Page introuvable</h1>
          <p className="mx-auto mt-4 max-w-md text-neutral-600">
            La page que vous recherchez n&apos;existe pas ou a été déplacée.
          </p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/">
              <Button className="gap-2">
                <Home className="size-4" strokeWidth={2} aria-hidden="true" />
                Retour à l&apos;accueil
              </Button>
            </Link>
            <Link to="/connexion">
              <Button variant="outline" className="gap-2">
                <LogIn className="size-4" strokeWidth={2} aria-hidden="true" />
                Se connecter
              </Button>
            </Link>
          </div>
        </div>
      </main>
      <PublicFooter />
    </div>
  );
}
