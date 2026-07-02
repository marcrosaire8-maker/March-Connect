import {
  Badge,
  Button,
  Card,
  EmptyState,
  LoadingState,
  Navbar,
  OffreCard,
  Skeleton,
} from "../components";

function Section({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mb-12">
      <h2 className="mb-1 text-h2 text-neutral-900">{title}</h2>
      {description && (
        <p className="mb-6 text-body text-neutral-600">{description}</p>
      )}
      {children}
    </section>
  );
}

function ColorSwatch({
  name,
  token,
  hex,
  textClass = "text-white",
}: {
  name: string;
  token: string;
  hex: string;
  textClass?: string;
}) {
  return (
    <div className="overflow-hidden rounded-lg border border-neutral-200">
      <div
        className={`flex h-20 items-end p-3 ${textClass}`}
        style={{ backgroundColor: hex }}
      >
        <span className="text-caption font-medium">{token}</span>
      </div>
      <div className="bg-surface-card px-3 py-2">
        <p className="text-body-sm font-medium text-neutral-800">{name}</p>
        <p className="font-mono text-caption text-neutral-500">{hex}</p>
      </div>
    </div>
  );
}

export function StyleGuidePage() {
  return (
    <div className="min-h-screen bg-surface">
      <header className="border-b border-neutral-200 bg-surface-card px-4 py-6 sm:px-8">
        <p className="mb-1 text-caption font-semibold uppercase tracking-wider text-accent">
          Dev only
        </p>
        <h1 className="text-display text-primary-dark">Charte graphique</h1>
        <p className="mt-2 max-w-2xl text-body text-neutral-600">
          Référence visuelle des tokens et composants réutilisables. À valider
          avant construction des pages fonctionnelles.
        </p>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-8">
        <Section
          title="Couleurs"
          description="Tokens définis dans tailwind.config.js — ne pas coder de couleurs en dur ailleurs."
        >
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <ColorSwatch name="Primaire marine" token="primary-dark" hex="#0F1E3D" />
            <ColorSwatch name="Primaire indigo" token="primary" hex="#1E3A8A" />
            <ColorSwatch name="Accent ambre" token="accent" hex="#D97706" textClass="text-primary-dark" />
            <ColorSwatch name="Accent doré" token="accent-light" hex="#F59E0B" textClass="text-primary-dark" />
            <ColorSwatch name="Fond général" token="surface" hex="#FAFAF9" textClass="text-neutral-700" />
            <ColorSwatch name="Texte secondaire" token="neutral-500" hex="#78716C" />
            <ColorSwatch name="Succès" token="success" hex="#059669" />
            <ColorSwatch name="Danger" token="danger" hex="#DC2626" />
          </div>
        </Section>

        <Section
          title="Typographie"
          description="Police Inter — corps minimum 16px (text-body)."
        >
          <Card className="space-y-4">
            <p className="text-display text-primary-dark">Display — 2.25rem</p>
            <p className="text-h1 text-neutral-900">Titre H1 — 1.875rem</p>
            <p className="text-h2 text-neutral-900">Titre H2 — 1.5rem</p>
            <p className="text-h3 text-neutral-900">Titre H3 — 1.25rem</p>
            <p className="text-body text-neutral-700">
              Corps de texte — 1rem (16px). Texte principal pour la lecture
              prolongée sur mobile et desktop.
            </p>
            <p className="text-body-sm text-neutral-600">
              Petit corps — 0.875rem. Métadonnées, labels secondaires.
            </p>
            <p className="text-caption text-neutral-500">
              Caption — 0.75rem. Badges, mentions légales.
            </p>
          </Card>
        </Section>

        <Section title="Boutons">
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primaire</Button>
            <Button variant="accent">S&apos;abonner</Button>
            <Button variant="secondary">Secondaire</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="primary" disabled>
              Désactivé
            </Button>
            <Button variant="accent" loading>
              Chargement
            </Button>
          </div>
          <p className="mt-4 text-body-sm text-neutral-500">
            L&apos;accent ambre est réservé aux actions principales. Contraste texte
            vérifié : texte marine (#0F1E3D) sur fond ambre.
          </p>
        </Section>

        <Section title="Badges">
          <div className="flex flex-wrap gap-3">
            <Badge variant="secteur">BTP / Travaux</Badge>
            <Badge variant="premium">Réservé aux abonnés</Badge>
            <Badge variant="actif">Abonnement actif</Badge>
            <Badge variant="inactif">Expiré</Badge>
            <Badge variant="neutral">Bénin</Badge>
          </div>
        </Section>

        <Section
          title="Cartes offre"
          description="Structure des cartes offre sur le tableau de bord."
        >
          <div className="grid gap-6 lg:grid-cols-2">
            <OffreCard
              titre="Construction de routes rurales — lot 3"
              organisme="Ministère des Infrastructures"
              dateLimite="15/08/2026"
              description="Contact : marches@infrastructures.bj — Tél. +229 21 30 00 00"
              contact={{
                email: "marches@infrastructures.bj",
                telephone: "+229 21 30 00 00",
                responsable: "Service des marchés",
                lieu_depot: "Direction des marchés publics, Cotonou",
              }}
              lienSource="https://www.marches-publics.bj/appels-doffres/1192684"
            />
            <OffreCard
              titre="Fourniture d'équipements informatiques"
              organisme="Agence de Développement"
              dateLimite="30/07/2026"
              lienSource="https://example.com/offre/123"
            />
          </div>
        </Section>

        <Section title="Card générique">
          <Card>
            <h3 className="mb-2 text-h3">Conteneur générique</h3>
            <p className="text-body text-neutral-600">
              Utilisé pour les panneaux, formulaires et blocs d&apos;information.
            </p>
          </Card>
        </Section>

        <Section title="Navbar">
          <div className="space-y-6 overflow-hidden rounded-lg border border-neutral-200">
            <div>
              <p className="bg-neutral-100 px-4 py-2 text-caption font-medium text-neutral-600">
                Visiteur non connecté
              </p>
              <Navbar />
            </div>
            <div>
              <p className="bg-neutral-100 px-4 py-2 text-caption font-medium text-neutral-600">
                Client connecté
              </p>
              <Navbar
                user={{ email: "client@example.com", role: "client" }}
              />
            </div>
            <div>
              <p className="bg-neutral-100 px-4 py-2 text-caption font-medium text-neutral-600">
                Administrateur
              </p>
              <Navbar user={{ email: "admin@example.com", role: "admin" }} />
            </div>
          </div>
        </Section>

        <Section title="États vides">
          <EmptyState
            title="Aucune offre trouvée"
            description="Essayez de modifier vos filtres ou élargissez votre recherche par pays ou secteur."
            actionLabel="Réinitialiser les filtres"
            onAction={() => undefined}
          />
        </Section>

        <Section title="Chargement">
          <div className="space-y-8">
            <div>
              <p className="mb-4 text-body-sm font-medium text-neutral-600">
                Skeleton (liste d&apos;offres)
              </p>
              <LoadingState count={2} />
            </div>
            <div>
              <p className="mb-4 text-body-sm font-medium text-neutral-600">
                Spinner
              </p>
              <LoadingState variant="spinner" />
            </div>
            <div className="flex gap-4">
              <Skeleton variant="circle" className="size-12" />
              <div className="flex-1 space-y-2">
                <Skeleton variant="text" className="w-full" />
                <Skeleton variant="text" className="w-3/4" />
              </div>
            </div>
          </div>
        </Section>

        <Section title="Accessibilité">
          <Card>
            <ul className="list-inside list-disc space-y-2 text-body text-neutral-700">
              <li>Corps de texte : 16px minimum (text-body)</li>
              <li>Focus visible au clavier sur tous les éléments interactifs</li>
              <li>Contraste accent : texte marine sur fond ambre (ratio AA)</li>
              <li>États loading avec aria-busy et aria-live</li>
              <li>Images décoratives avec alt vide ou aria-hidden</li>
            </ul>
          </Card>
        </Section>
      </main>
    </div>
  );
}
