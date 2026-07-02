import { FormEvent, useCallback, useEffect, useState } from "react";
import { Badge } from "./Badge";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { suivisSitesApi } from "../api";
import type { SuiviSite } from "../api/types";
import { formatDateTime } from "../lib/format";

function StatusBadge({ statut }: { statut: string }) {
  const variant =
    statut === "succes" ? "actif" : statut === "echec" ? "inactif" : "neutral";
  return <Badge variant={variant}>{statut}</Badge>;
}

interface MesSitesSectionProps {
  onChange?: () => void;
  compact?: boolean;
}

export function MesSitesSection({ onChange, compact = false }: MesSitesSectionProps) {
  const [sites, setSites] = useState<SuiviSite[]>([]);
  const [loading, setLoading] = useState(true);
  const [url, setUrl] = useState("");
  const [adding, setAdding] = useState(false);
  const [refreshingId, setRefreshingId] = useState<string | null>(null);
  const [removingId, setRemovingId] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setSites(await suivisSitesApi.list());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const notifyChange = () => {
    onChange?.();
  };

  const handleAdd = async (e: FormEvent) => {
    e.preventDefault();
    setAdding(true);
    setMessage(null);
    try {
      await suivisSitesApi.add(url);
      setMessage("Site ajouté. L'analyse démarre en arrière-plan — actualisez dans quelques instants.");
      setUrl("");
      await load();
      notifyChange();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur lors de l'ajout");
    } finally {
      setAdding(false);
    }
  };

  const handleRefresh = async (siteId: string) => {
    setRefreshingId(siteId);
    setMessage(null);
    try {
      const result = await suivisSitesApi.refresh(siteId);
      setMessage(result.message ?? "Analyse lancée en arrière-plan.");
      window.setTimeout(() => {
        void load().then(notifyChange);
      }, 4000);
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur scraping");
    } finally {
      setRefreshingId(null);
    }
  };

  const handleRemove = async (siteId: string) => {
    setRemovingId(siteId);
    setMessage(null);
    try {
      await suivisSitesApi.remove(siteId);
      setMessage("Suivi supprimé.");
      await load();
      notifyChange();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur suppression");
    } finally {
      setRemovingId(null);
    }
  };

  return (
    <div className={compact ? "" : "dashboard-filter-card mb-8"}>
      {!compact && (
        <>
          <h2 className="mb-1 text-base font-semibold text-neutral-900">Suivre un site</h2>
          <p className="mb-4 text-sm text-neutral-500">
            Collez l&apos;URL d&apos;un portail de marchés publics. L&apos;analyse se lance
            automatiquement sans bloquer la page.
          </p>
        </>
      )}

      <form
        onSubmit={handleAdd}
        className={compact ? "mb-3 space-y-2" : "mb-4 grid gap-3 sm:grid-cols-[1fr_auto]"}
      >
        <input
          required
          type="url"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://exemple.gov/..."
          className="dashboard-input"
        />
        <Button type="submit" variant="primary" loading={adding} fullWidth={compact}>
          {compact ? "Ajouter un site" : "Ajouter et analyser"}
        </Button>
      </form>

      {message && (
        <p className="mb-4 rounded-xl border border-brand/20 bg-brand-muted/40 p-3 text-sm text-neutral-700">
          {message}
        </p>
      )}

      {loading ? (
        <LoadingState variant="spinner" />
      ) : sites.length > 0 ? (
        <ul className={compact ? "space-y-2" : "space-y-3 border-t border-neutral-200 pt-4"}>
          {sites.map((site) => (
            <li
              key={site.id}
              className={compact
                ? "dashboard-widget-item"
                : "flex flex-wrap items-start justify-between gap-3 rounded-xl border border-neutral-200/60 bg-white/80 p-4"}
            >
              <div className="min-w-0 flex-1">
                <p className={compact ? "text-sm font-medium text-neutral-900" : "font-medium text-neutral-900"}>
                  {site.nom}
                </p>
                <a
                  href={site.url_base}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-0.5 block truncate text-xs text-brand hover:underline"
                >
                  {site.url_base}
                </a>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {site.dernier_statut ? (
                    <StatusBadge statut={site.dernier_statut} />
                  ) : (
                    <Badge variant="neutral">en attente</Badge>
                  )}
                  {site.nb_offres_trouvees != null && (
                    <Badge variant="neutral">{site.nb_offres_trouvees} offre(s)</Badge>
                  )}
                  {site.nb_offres_nouvelles != null && site.nb_offres_nouvelles > 0 && (
                    <Badge variant="neutral">{site.nb_offres_nouvelles} nouvelle(s)</Badge>
                  )}
                </div>
                <p className="mt-1 text-caption text-neutral-500">
                  Dernière analyse : {formatDateTime(site.derniere_execution)}
                </p>
                {site.message_erreur && (
                  <p className="mt-1 text-body-sm text-danger">{site.message_erreur}</p>
                )}
              </div>
              <div className={compact ? "dashboard-touch-row mt-2" : "flex flex-wrap gap-2"}>
                <Button
                  variant="secondary"
                  loading={refreshingId === site.id}
                  onClick={() => void handleRefresh(site.id)}
                  className={compact ? "dashboard-touch-btn flex-1 px-3 text-xs" : undefined}
                >
                  Actualiser
                </Button>
                <Button
                  variant="outline"
                  loading={removingId === site.id}
                  onClick={() => void handleRemove(site.id)}
                  className={compact ? "dashboard-touch-btn flex-1 px-3 text-xs" : undefined}
                >
                  Supprimer
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className={compact ? "text-xs text-neutral-500" : "border-t border-neutral-200 pt-4 text-body-sm text-neutral-500"}>
          Aucun site suivi. Ajoutez une URL pour commencer.
        </p>
      )}
    </div>
  );
}
