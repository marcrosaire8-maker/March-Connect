import { useState } from "react";
import { Link } from "react-router-dom";
import { Bell, Globe, Landmark, LayoutDashboard, type LucideIcon } from "lucide-react";
import { SiteBrand } from "../components/SiteBrand";
import { cn } from "../lib/cn";
import { HERO_BG_SRC, SITE_NAME, SITE_TAGLINE } from "../lib/branding";

const heroNavLinks = [
  { to: "/", label: "Accueil" },
  { to: "/a-propos", label: "À propos" },
  { to: "/contact", label: "Contact" },
];

const features: { title: string; description: string; Icon: LucideIcon }[] = [
  {
    title: "Veille automatisée",
    description:
      "Collecte régulière des appels d'offres depuis les plateformes officielles d'Afrique de l'Ouest et sources complémentaires.",
    Icon: Globe,
  },
  {
    title: "Alertes personnalisées",
    description:
      "Recevez par e-mail les offres correspondant à vos secteurs, pays et mots-clés — une offre par message, toutes les 15 minutes.",
    Icon: Bell,
  },
  {
    title: "Tableau de bord clair",
    description:
      "Filtrez par secteur, pays et date limite. Consultez le calendrier des échéances et enregistrez vos favoris.",
    Icon: LayoutDashboard,
  },
  {
    title: "Sources officielles",
    description:
      "Bénin, Sénégal, Togo, Côte d'Ivoire, BOAMP France et autres portails publics référencés et mis à jour automatiquement.",
    Icon: Landmark,
  },
];

const steps = [
  { step: "1", title: "Créez votre compte", text: "Inscription gratuite en quelques secondes." },
  { step: "2", title: "Configurez vos critères", text: "Choisissez secteurs et pays d'intérêt." },
  { step: "3", title: "Recevez les alertes", text: "Les offres actives arrivent dans votre boîte mail." },
];

export function LandingPage() {
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <div>
      {/* Hero */}
      <section className="relative flex min-h-screen min-h-dvh flex-col overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: `url(${HERO_BG_SRC})` }}
          aria-hidden="true"
        />
        <div className="absolute inset-0 bg-brand-900/30" aria-hidden="true" />
        <div className="absolute inset-0 bg-black/15" aria-hidden="true" />
        <div
          className="pointer-events-none absolute inset-y-0 left-0 z-[1] w-full max-w-[min(100%,52rem)] bg-gradient-to-r from-black/60 via-black/35 to-transparent"
          aria-hidden="true"
        />

        {/* Navigation intégrée */}
        <header className="relative z-20 px-4 pt-4 sm:px-6 lg:px-8">
          <div className="mx-auto grid max-w-6xl grid-cols-[1fr_auto_1fr] items-center gap-4">
            <SiteBrand to="/" size="lg" variant="light" className="justify-self-start gap-3" />

            <nav
              className="hidden items-center justify-center gap-8 md:flex"
              aria-label="Navigation principale"
            >
              {heroNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className={cn(
                    "text-sm font-medium transition-colors",
                    link.to === "/"
                      ? "text-white"
                      : "text-white/75 hover:text-white"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </nav>

            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                className="inline-flex size-10 items-center justify-center rounded-lg text-white/90 hover:bg-white/10 md:hidden"
                aria-expanded={mobileNavOpen}
                aria-label={mobileNavOpen ? "Fermer le menu" : "Ouvrir le menu"}
                onClick={() => setMobileNavOpen((o) => !o)}
              >
                <svg className="size-6" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" aria-hidden="true">
                  {mobileNavOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>
              <Link
                to="/inscription"
                className="hidden rounded-full bg-white/85 px-5 py-2.5 text-sm font-semibold text-neutral-900 shadow-sm backdrop-blur-sm transition hover:bg-white md:inline-flex"
              >
                S&apos;inscrire
              </Link>
            </div>
          </div>

          {mobileNavOpen && (
            <nav className="mx-auto mt-3 flex max-w-6xl flex-col gap-1 rounded-2xl border border-white/15 bg-black/30 p-3 backdrop-blur-md md:hidden">
              {heroNavLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileNavOpen(false)}
                  className="rounded-lg px-3 py-2.5 text-sm font-medium text-white/90 hover:bg-white/10"
                >
                  {link.label}
                </Link>
              ))}
              <Link
                to="/inscription"
                onClick={() => setMobileNavOpen(false)}
                className="mt-1 rounded-full bg-white/85 px-4 py-2.5 text-center text-sm font-semibold text-neutral-900"
              >
                S&apos;inscrire
              </Link>
            </nav>
          )}
        </header>

        {/* Contenu principal */}
        <div className="relative z-10 flex flex-1 items-center px-4 sm:px-6 lg:px-8">
          <div className="mx-auto w-full max-w-6xl">
            <div className="max-w-lg space-y-4">
              <h1 className="text-2xl font-bold leading-snug tracking-tight text-white drop-shadow-[0_2px_8px_rgba(0,0,0,0.45)] sm:text-3xl lg:text-[2rem] lg:leading-tight">
                Ne manquez plus aucun{" "}
                <span className="text-brand-light">appel d&apos;offres</span>
              </h1>
              <p className="text-base font-medium text-white drop-shadow-[0_1px_4px_rgba(0,0,0,0.7)] sm:text-lg">
                {SITE_TAGLINE}
              </p>
              <p className="max-w-md text-sm leading-relaxed text-white/90 drop-shadow-[0_1px_4px_rgba(0,0,0,0.75)] sm:text-base">
                {SITE_NAME} centralise la veille, classe les opportunités par secteur et vous alerte
                dès qu&apos;une offre correspond à votre profil.
              </p>
              <div className="flex flex-wrap gap-3 pt-1">
                <Link
                  to="/inscription"
                  className="group inline-flex min-h-12 items-center gap-2 rounded-full border border-white/35 bg-white/15 px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm transition hover:border-white/50 hover:bg-white/25"
                >
                  Commencer gratuitement
                  <span className="transition-transform group-hover:translate-x-0.5" aria-hidden="true">
                    →
                  </span>
                </Link>
                <Link
                  to="/connexion"
                  className="inline-flex min-h-12 items-center rounded-full border border-white/25 bg-transparent px-6 py-3 text-sm font-semibold text-white/90 transition hover:border-white/40 hover:bg-white/10 hover:text-white"
                >
                  Se connecter
                </Link>
              </div>
            </div>
          </div>
        </div>

        {/* Texte complémentaire bas gauche */}
        <div className="absolute inset-x-0 bottom-0 z-10">
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-black/25 to-transparent"
            aria-hidden="true"
          />
          <div className="relative px-4 pb-10 pt-12 sm:px-6 sm:pb-12 lg:px-8">
            <div className="mx-auto max-w-6xl">
              <p className="text-xs font-medium uppercase tracking-wide text-white/80 drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
                Plateforme de veille
              </p>
              <p className="mt-0.5 text-sm text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.8)]">
                Des centaines d&apos;offres suivies
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-gradient-to-b from-surface via-brand-muted/30 to-brand-muted/50 py-14 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <p className="mb-4 inline-flex rounded-full border border-brand/25 bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand">
              Fonctionnalités
            </p>
            <h2 className="text-2xl font-bold text-neutral-900 sm:text-3xl">
              Tout ce dont vous avez besoin
            </h2>
            <p className="mx-auto mt-3 max-w-2xl text-neutral-600">
              Une solution complète pour les entreprises, ONG et consultants en marchés publics.
            </p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {features.map(({ title, description, Icon }) => (
              <div
                key={title}
                className="group rounded-2xl border border-transparent bg-white p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand-light hover:shadow-card-hover"
              >
                <div className="flex size-12 items-center justify-center rounded-full bg-brand-muted transition-colors group-hover:bg-brand/15">
                  <Icon className="size-6 text-brand" strokeWidth={2} aria-hidden="true" />
                </div>
                <h3 className="mt-5 font-semibold text-neutral-900">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-neutral-500">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Steps */}
      <section className="bg-white py-14 sm:py-20">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <div className="mb-12 text-center">
            <p className="mb-4 inline-flex rounded-full border border-brand/20 bg-brand-muted px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand">
              En 3 étapes
            </p>
            <h2 className="text-2xl font-bold text-neutral-900 sm:text-3xl">Comment ça marche ?</h2>
          </div>

          <div className="relative">
            <div
              className="pointer-events-none absolute left-[16.67%] right-[16.67%] top-7 hidden h-0.5 bg-gradient-to-r from-brand/10 via-brand/35 to-brand/10 md:block"
              aria-hidden="true"
            />
            <div className="grid gap-10 md:grid-cols-3 md:gap-8">
              {steps.map((s) => (
                <div key={s.step} className="relative z-10 text-center">
                  <div className="mx-auto flex size-14 items-center justify-center rounded-full bg-brand text-xl font-bold text-white shadow-lg shadow-brand/30">
                    {s.step}
                  </div>
                  <h3 className="mt-5 font-semibold text-neutral-900">{s.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-neutral-500">{s.text}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-neutral-50 pb-16 pt-4 sm:pb-20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-brand via-brand to-brand-dark px-8 py-12 text-center text-white shadow-2xl shadow-brand/25 sm:px-12 sm:py-14">
            <div
              className="pointer-events-none absolute -right-16 -top-16 size-56 rounded-full bg-white/10"
              aria-hidden="true"
            />
            <div
              className="pointer-events-none absolute -bottom-20 -left-12 size-72 rounded-full bg-black/10"
              aria-hidden="true"
            />
            <div
              className="pointer-events-none absolute right-1/4 top-1/3 size-24 rotate-12 rounded-2xl bg-white/5"
              aria-hidden="true"
            />
            <div
              className="pointer-events-none absolute bottom-1/4 right-8 size-16 -rotate-6 rounded-full bg-white/5"
              aria-hidden="true"
            />

            <div className="relative">
              <h2 className="text-2xl font-bold sm:text-3xl">Prêt à découvrir les opportunités ?</h2>
              <p className="mx-auto mt-3 max-w-md text-white/90">
                Rejoignez {SITE_NAME} et configurez vos alertes en moins de deux minutes.
              </p>
              <div className="mt-8 flex flex-wrap justify-center gap-3">
                <Link
                  to="/inscription"
                  className="group inline-flex min-h-12 items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-brand shadow-lg transition hover:bg-neutral-50"
                >
                  Créer un compte
                  <span className="transition-transform group-hover:translate-x-0.5" aria-hidden="true">
                    →
                  </span>
                </Link>
                <Link
                  to="/a-propos"
                  className="inline-flex min-h-12 items-center rounded-full border border-white/40 bg-white/10 px-6 py-3 text-sm font-semibold text-white backdrop-blur-sm transition hover:border-white/60 hover:bg-white/20"
                >
                  En savoir plus
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
