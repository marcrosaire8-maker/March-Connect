import { cn } from "../../lib/cn";
import { PAYS_OPTIONS } from "../../lib/format";

interface FilterToolbarProps {
  pays: string;
  onPaysChange: (pays: string) => void;
  total: number;
  loading?: boolean;
  hasFilters?: boolean;
  onClear?: () => void;
  dateLimite?: string;
  onDateLimiteChange?: (value: string) => void;
  showDateFilter?: boolean;
  paysOptions?: readonly string[];
  allPaysLabel?: string;
  search?: string;
  onSearchChange?: (value: string) => void;
  favorisOnly?: boolean;
  onFavorisOnlyChange?: (value: boolean) => void;
  mesSitesOnly?: boolean;
  onMesSitesOnlyChange?: (value: boolean) => void;
}

export function FilterToolbar({
  pays,
  onPaysChange,
  total,
  loading,
  hasFilters,
  onClear,
  dateLimite = "",
  onDateLimiteChange,
  showDateFilter = false,
  paysOptions = PAYS_OPTIONS,
  allPaysLabel = "Tous",
  search = "",
  onSearchChange,
  favorisOnly = false,
  onFavorisOnlyChange,
  mesSitesOnly = false,
  onMesSitesOnlyChange,
}: FilterToolbarProps) {
  return (
    <div className="dashboard-toolbar">
      <div className="dashboard-toolbar-filters">
        {onSearchChange && (
          <label className="flex min-w-0 flex-col gap-1.5 sm:min-w-[220px] sm:flex-1">
            <span className="dashboard-toolbar-label">Recherche</span>
            <input
              type="search"
              value={search}
              onChange={(e) => onSearchChange(e.target.value)}
              placeholder="Titre, organisme, mot-clé…"
              className="dashboard-input w-full"
            />
          </label>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <span className="dashboard-toolbar-label">Pays</span>
          <button
            type="button"
            onClick={() => onPaysChange("")}
            className={cn("dashboard-chip", !pays && "dashboard-chip-active")}
          >
            {allPaysLabel}
          </button>
          {paysOptions.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => onPaysChange(p === pays ? "" : p)}
              className={cn("dashboard-chip", pays === p && "dashboard-chip-active")}
            >
              {p}
            </button>
          ))}
        </div>

        {showDateFilter && onDateLimiteChange && (
          <label className="flex min-w-0 flex-col gap-1.5 sm:flex-row sm:items-center sm:gap-2">
            <span className="dashboard-toolbar-label shrink-0">Date limite après</span>
            <input
              type="date"
              value={dateLimite}
              onChange={(e) => onDateLimiteChange(e.target.value)}
              className="dashboard-input w-full min-w-0 sm:w-auto"
            />
          </label>
        )}

        {(onFavorisOnlyChange || onMesSitesOnlyChange) && (
          <div className="flex flex-wrap items-center gap-2">
            {onFavorisOnlyChange && (
              <button
                type="button"
                onClick={() => onFavorisOnlyChange(!favorisOnly)}
                className={cn("dashboard-chip", favorisOnly && "dashboard-chip-active")}
              >
                Favoris
              </button>
            )}
            {onMesSitesOnlyChange && (
              <button
                type="button"
                onClick={() => onMesSitesOnlyChange(!mesSitesOnly)}
                className={cn("dashboard-chip", mesSitesOnly && "dashboard-chip-active")}
              >
                Mes sites
              </button>
            )}
          </div>
        )}
      </div>

      <div className="dashboard-toolbar-meta">
        <span className="dashboard-live-badge">
          <span className="dashboard-live-dot" />
          {loading ? "Chargement…" : `${total.toLocaleString("fr-FR")} résultat${total > 1 ? "s" : ""}`}
        </span>
        {hasFilters && onClear && (
          <button type="button" onClick={onClear} className="dashboard-clear-btn">
            Effacer les filtres
          </button>
        )}
      </div>
    </div>
  );
}
