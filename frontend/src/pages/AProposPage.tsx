import { Link } from "react-router-dom";
import { Globe, Lightbulb, Target, Users, type LucideIcon } from "lucide-react";
import { SITE_NAME, SITE_TAGLINE } from "../lib/branding";

const values: { title: string; text: string; Icon: LucideIcon }[] = [
  {
    title: "Notre mission",
    text: "Faciliter l'accès aux marchés publics en Afrique de l'Ouest pour les PME, grandes entreprises, ONG et consultants qui souhaitent identifier rapidement les opportunités pertinentes.",
    Icon: Target,
  },
  {
    title: "Notre approche",
    text: "Nous agrégeons les données depuis les portails officiels, les classons par secteur et pays, puis les diffusons via un tableau de bord intuitif et des alertes e-mail personnalisées.",
    Icon: Lightbulb,
  },
  {
    title: "Nos utilisateurs",
    text: "Entrepreneurs, responsables commerciaux, chargés de veille et structures de développement qui ont besoin d'une vision claire et à jour du paysage des appels d'offres régionaux.",
    Icon: Users,
  },
];

const countries = [
  { name: "Bénin", flag: "🇧🇯" },
  { name: "Sénégal", flag: "🇸🇳" },
  { name: "Togo", flag: "🇹🇬" },
  { name: "Côte d'Ivoire", flag: "🇨🇮" },
  { name: "Burkina Faso", flag: "🇧🇫" },
  { name: "Mali", flag: "🇲🇱" },
  { name: "Niger", flag: "🇳🇪" },
  { name: "Guinée", flag: "🇬🇳" },
  { name: "France (BOAMP)", flag: "🇫🇷" },
];

export function AProposPage() {
  return (
    <div className="bg-gradient-to-b from-white via-surface to-brand-muted/40">
      <div className="mx-auto max-w-4xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        {/* En-tête */}
        <header className="mb-14 text-center">
          <p className="mb-4 inline-flex rounded-full border border-brand/25 bg-brand/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-brand">
            À propos
          </p>
          <h1 className="text-3xl font-bold tracking-tight text-neutral-900 sm:text-4xl lg:text-[2.5rem] lg:leading-tight">
            À propos de <span className="text-brand">{SITE_NAME}</span>
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-neutral-600">{SITE_TAGLINE}</p>
        </header>

        {/* Cartes valeurs */}
        <section className="mb-14">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {values.map(({ title, text, Icon }) => (
              <div
                key={title}
                className="group rounded-2xl border border-transparent bg-white p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-brand-light hover:shadow-card-hover sm:p-7"
              >
                <div className="flex size-12 items-center justify-center rounded-full bg-brand-muted transition-colors group-hover:bg-brand/15">
                  <Icon className="size-6 text-brand" strokeWidth={2} aria-hidden="true" />
                </div>
                <h2 className="mt-5 text-lg font-semibold text-neutral-900">{title}</h2>
                <p className="mt-3 text-sm leading-relaxed text-neutral-600">{text}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Pays et sources */}
        <section className="mb-16 rounded-2xl border-2 border-brand/25 bg-brand-muted/50 p-6 sm:p-8">
          <div className="flex items-start gap-3">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-brand/15">
              <Globe className="size-5 text-brand" strokeWidth={2} aria-hidden="true" />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="text-lg font-semibold text-neutral-900">Pays et sources couverts</h2>
              <p className="mt-2 text-sm leading-relaxed text-neutral-600">
                La plateforme évolue en continu. Voici les principales zones et sources actuellement
                suivies :
              </p>
            </div>
          </div>
          <ul className="mt-6 flex flex-wrap gap-3">
            {countries.map(({ name, flag }) => (
              <li key={name}>
                <span className="inline-flex items-center gap-2 rounded-full border border-brand/15 bg-white px-3.5 py-1.5 text-sm font-medium text-neutral-700 shadow-sm transition-colors hover:border-brand/30 hover:bg-brand/15">
                  <span aria-hidden="true">{flag}</span>
                  {name}
                </span>
              </li>
            ))}
          </ul>
        </section>

        {/* CTA */}
        <section className="pb-4 pt-4 text-center">
          <Link
            to="/inscription"
            className="group inline-flex min-h-12 items-center gap-2 rounded-full bg-brand px-8 py-3 text-sm font-semibold text-white shadow-lg shadow-brand/25 transition-all duration-200 hover:scale-105 hover:bg-brand-dark hover:shadow-xl hover:shadow-brand/30"
          >
            Rejoindre {SITE_NAME}
            <span className="transition-transform group-hover:translate-x-0.5" aria-hidden="true">
              →
            </span>
          </Link>
        </section>
      </div>
    </div>
  );
}
