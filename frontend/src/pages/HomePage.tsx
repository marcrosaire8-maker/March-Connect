import { useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button, EmptyState, LoadingState, MesSitesSection, NotificationEmailsPanel, OffreCard } from "../components";
import { SecteurSidebar } from "../components/SecteurSidebar";
import { FilterToolbar } from "../components/dashboard/FilterToolbar";
import { DashboardSection } from "../components/dashboard/DashboardSection";
import {
  DashboardPage,
  IconGlobe,
  IconOffers,
  IconSectors,
  MetricCard,
} from "../components/dashboard/DashboardPage";
import { offresApi, secteursApi, abonnesApi, favorisApi } from "../api";
import { clearPrefsConfiguredForEmail, hasPrefsConfiguredForEmail } from "../api/client";
import type { Abonne, Offre, Secteur } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { formatDate, PAYS_OPTIONS } from "../lib/format";

function abonneHasActivePrefs(abonne: Abonne | null | undefined): boolean {
  if (!abonne) return false;
  return abonne.secteurs_suivis.length > 0 && abonne.pays_suivis.length > 0;
}

interface OffresListProps {
  title?: string;
}

export function OffresList({ title = "Appels d'offres" }: OffresListProps) {
  const { isAuthenticated, loading: authLoading, user } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [offres, setOffres] = useState<Offre[]>([]);
  const [secteurs, setSecteurs] = useState<Secteur[]>([]);
  const [abonne, setAbonne] = useState<Abonne | null>(null);
  const [secteurMap, setSecteurMap] = useState<Record<string, string>>({});
  const [selectedSecteur, setSelectedSecteur] = useState<string>();
  const [pays, setPays] = useState("");
  const [dateLimite, setDateLimite] = useState("");
  const [search, setSearch] = useState("");
  const [favorisOnly, setFavorisOnly] = useState(false);
  const [mesSitesOnly, setMesSitesOnly] = useState(false);
  const [favoriIds, setFavoriIds] = useState<Set<string>>(new Set());
  const [favLoadingId, setFavLoadingId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [abonneLoaded, setAbonneLoaded] = useState(false);

  const loadSecteurs = useCallback(async () => {
    const data = await secteursApi.list();
    setSecteurs(data);
    const map: Record<string, string> = {};
    data.forEach((s) => {
      map[s.id] = s.nom;
    });
    setSecteurMap(map);
  }, []);

  const loadAbonne = useCallback(async () => {
    if (!isAuthenticated) {
      setAbonne(null);
      setAbonneLoaded(true);
      return;
    }
    try {
      setAbonne(await abonnesApi.me());
    } catch {
      setAbonne(null);
    } finally {
      setAbonneLoaded(true);
    }
  }, [isAuthenticated]);

  const hasConfiguredPrefs = abonneHasActivePrefs(abonne);

  const loadOffres = useCallback(async () => {
    if (!hasConfiguredPrefs) {
      setOffres([]);
      setTotal(0);
      setTotalPages(0);
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await offresApi.list({
        page,
        page_size: 12,
        secteur_id: selectedSecteur,
        pays: pays || undefined,
        date_limite_apres: dateLimite || undefined,
        q: search.trim() || undefined,
        favoris_only: favorisOnly,
        mes_sites_only: mesSitesOnly,
      });
      setOffres(data.items);
      setTotalPages(data.total_pages);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur de chargement");
    } finally {
      setLoading(false);
    }
  }, [page, selectedSecteur, pays, dateLimite, search, favorisOnly, mesSitesOnly, hasConfiguredPrefs]);

  const loadFavoris = useCallback(async () => {
    if (!hasConfiguredPrefs) {
      setFavoriIds(new Set());
      return;
    }
    try {
      const ids = await favorisApi.list();
      setFavoriIds(new Set(ids));
    } catch {
      setFavoriIds(new Set());
    }
  }, [hasConfiguredPrefs]);

  const toggleFavori = async (offreId: string) => {
    setFavLoadingId(offreId);
    try {
      if (favoriIds.has(offreId)) {
        await favorisApi.remove(offreId);
        setFavoriIds((prev) => {
          const next = new Set(prev);
          next.delete(offreId);
          return next;
        });
      } else {
        await favorisApi.add(offreId);
        setFavoriIds((prev) => new Set(prev).add(offreId));
      }
      if (favorisOnly) {
        void loadOffres();
      }
    } finally {
      setFavLoadingId(null);
    }
  };

  useEffect(() => {
    if (!abonneLoaded) return;
    void loadSecteurs();
    void loadFavoris();
  }, [abonneLoaded, loadSecteurs, loadFavoris]);

  useEffect(() => {
    if (authLoading) return;
    setAbonneLoaded(false);
    void loadAbonne();
  }, [authLoading, loadAbonne, location.key]);

  useEffect(() => {
    if (authLoading || !abonneLoaded || !isAuthenticated) return;
    if (
      hasPrefsConfiguredForEmail(user?.email) &&
      !abonneHasActivePrefs(abonne)
    ) {
      clearPrefsConfiguredForEmail(user!.email);
      navigate("/mes-preferences", { replace: true });
    }
  }, [abonne, abonneLoaded, authLoading, isAuthenticated, navigate, user?.email]);

  const singleSecteurId =
    hasConfiguredPrefs && abonne!.secteurs_suivis.length === 1
      ? abonne!.secteurs_suivis[0]
      : undefined;

  useEffect(() => {
    if (!hasConfiguredPrefs) return;
    if (singleSecteurId) {
      setSelectedSecteur(singleSecteurId);
      return;
    }
    if (selectedSecteur && !abonne!.secteurs_suivis.includes(selectedSecteur)) {
      setSelectedSecteur(undefined);
    }
    if (pays && !abonne!.pays_suivis.includes(pays)) {
      setPays("");
    }
  }, [abonne, hasConfiguredPrefs, selectedSecteur, pays, singleSecteurId]);

  useEffect(() => {
    if (authLoading || !abonneLoaded) return;
    void loadOffres();
  }, [authLoading, abonneLoaded, abonne, loadOffres]);

  useEffect(() => {
    setPage(1);
  }, [selectedSecteur, pays, dateLimite, search, favorisOnly, mesSitesOnly]);

  const clearFilters = () => {
    if (!singleSecteurId) {
      setSelectedSecteur(undefined);
    }
    setPays("");
    setDateLimite("");
    setSearch("");
    setFavorisOnly(false);
    setMesSitesOnly(false);
  };

  const hasFilters = Boolean(
    selectedSecteur || pays || dateLimite || search || favorisOnly || mesSitesOnly
  );
  const selectedSecteurName = selectedSecteur ? secteurMap[selectedSecteur] : null;

  const visibleSecteurs = hasConfiguredPrefs
    ? secteurs.filter((s) => abonne!.secteurs_suivis.includes(s.id))
    : [];

  const visiblePays = hasConfiguredPrefs
    ? PAYS_OPTIONS.filter((p) => abonne!.pays_suivis.includes(p))
    : [];

  return (
    <DashboardPage
      layout="fill"
      title={title}
      subtitle="Offres limitées aux secteurs et pays choisis dans Mon compte"
    >
      <div className="dashboard-offres-toolbar shrink-0 space-y-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:gap-4">
          <MetricCard
            label="Offres actives"
            value={total.toLocaleString("fr-FR")}
            hint="Dans votre sélection"
            accent="green"
            icon={<IconOffers />}
          />
          <MetricCard
            label="Secteurs"
            value={visibleSecteurs.length}
            hint="Dans votre sélection"
            accent="teal"
            icon={<IconSectors />}
          />
          <MetricCard
            label="Zone couverte"
            value={`${visiblePays.length} pays`}
            hint={visiblePays.join(" · ")}
            accent="gold"
            icon={<IconGlobe />}
          />
        </div>

        {hasConfiguredPrefs && abonne && (
          <p className="rounded-lg border border-neutral-200 bg-neutral-50 px-4 py-3 text-body-sm text-neutral-700">
            Votre sélection :{" "}
            {abonne.secteurs_suivis
              .map((id) => secteurMap[id])
              .filter(Boolean)
              .join(", ")}{" "}
            · {abonne.pays_suivis.join(", ")}.{" "}
            <Link to="/mon-compte" className="font-medium text-neutral-900 underline-offset-2 hover:underline">
              Modifier dans Mon compte
            </Link>
          </p>
        )}

        <FilterToolbar
          pays={pays}
          onPaysChange={setPays}
          paysOptions={visiblePays}
          allPaysLabel="Tous vos pays"
          total={total}
          loading={loading}
          hasFilters={hasFilters}
          onClear={clearFilters}
          dateLimite={dateLimite}
          onDateLimiteChange={setDateLimite}
          showDateFilter
          search={search}
          onSearchChange={setSearch}
          favorisOnly={favorisOnly}
          onFavorisOnlyChange={setFavorisOnly}
          mesSitesOnly={mesSitesOnly}
          onMesSitesOnlyChange={setMesSitesOnly}
        />
      </div>

      <div className="dashboard-main-grid dashboard-main-grid-fill">
        <DashboardSection
          title="Secteurs"
          description="Affinez par domaine d'activité"
          className="dashboard-col-filters dashboard-col-pinned"
        >
          <SecteurSidebar
            secteurs={visibleSecteurs}
            selectedId={selectedSecteur}
            onSelect={setSelectedSecteur}
            allLabel="Tous vos secteurs"
            showAllOption={!singleSecteurId}
          />
        </DashboardSection>

        <div className="dashboard-col-feed dashboard-col-feed-scroll min-w-0">
          {(selectedSecteurName || pays || dateLimite || search || favorisOnly || mesSitesOnly) && (
            <div className="dashboard-active-filters">
              {selectedSecteurName && !singleSecteurId && (
                <span className="dashboard-active-tag">
                  Secteur : {selectedSecteurName}
                  <button type="button" onClick={() => setSelectedSecteur(undefined)} aria-label="Retirer le filtre secteur">×</button>
                </span>
              )}
              {pays && (
                <span className="dashboard-active-tag">
                  Pays : {pays}
                  <button type="button" onClick={() => setPays("")} aria-label="Retirer le filtre pays">×</button>
                </span>
              )}
              {dateLimite && (
                <span className="dashboard-active-tag">
                  Date limite après : {dateLimite}
                  <button type="button" onClick={() => setDateLimite("")} aria-label="Retirer le filtre date">×</button>
                </span>
              )}
              {search && (
                <span className="dashboard-active-tag">
                  Recherche : {search}
                  <button type="button" onClick={() => setSearch("")} aria-label="Retirer la recherche">×</button>
                </span>
              )}
              {favorisOnly && (
                <span className="dashboard-active-tag">
                  Favoris
                  <button type="button" onClick={() => setFavorisOnly(false)} aria-label="Retirer le filtre favoris">×</button>
                </span>
              )}
              {mesSitesOnly && (
                <span className="dashboard-active-tag">
                  Mes sites
                  <button type="button" onClick={() => setMesSitesOnly(false)} aria-label="Retirer le filtre mes sites">×</button>
                </span>
              )}
            </div>
          )}

          {error && (
            <div className="dashboard-alert dashboard-alert-error">{error}</div>
          )}

          {loading ? (
            <LoadingState count={6} />
          ) : offres.length === 0 ? (
            <EmptyState
              title="Aucune offre trouvée"
              description="Aucune offre dans votre sélection actuelle. Modifiez vos secteurs ou pays dans Mon compte."
            />
          ) : (
            <>
              <div className="dashboard-offres-grid">
                {offres.map((offre, i) => (
                  <OffreCard
                    key={offre.id}
                    offreId={offre.id}
                    titre={offre.titre}
                    organisme={offre.organisme}
                    description={offre.description}
                    contact={offre.contact}
                    dateLimite={
                      offre.date_limite ? formatDate(offre.date_limite) : undefined
                    }
                    lienSource={offre.lien_source}
                    isFavori={favoriIds.has(offre.id)}
                    favoriLoading={favLoadingId === offre.id}
                    onToggleFavori={() => void toggleFavori(offre.id)}
                    style={{ animationDelay: `${i * 50}ms` }}
                  />
                ))}
              </div>

              {totalPages > 1 && (
                <nav className="dashboard-pagination" aria-label="Pagination">
                  <Button
                    variant="secondary"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    ← Précédent
                  </Button>
                  <span className="dashboard-pagination-info">
                    Page <strong>{page}</strong> sur {totalPages}
                  </span>
                  <Button
                    variant="secondary"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Suivant →
                  </Button>
                </nav>
              )}
            </>
          )}
        </div>

        <aside className="dashboard-col-widgets dashboard-col-pinned space-y-4">
          <DashboardSection
            title="Mes sites"
            description="Portails que vous suivez"
          >
            <MesSitesSection compact onChange={loadOffres} />
          </DashboardSection>

          <DashboardSection
            title="Alertes email"
            description="Notifications personnalisées"
          >
            <NotificationEmailsPanel embedded />
          </DashboardSection>
        </aside>
      </div>
    </DashboardPage>
  );
}

export function HomePage() {
  return <OffresList />;
}
