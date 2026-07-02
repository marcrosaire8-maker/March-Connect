import { cn } from "../lib/cn";
import type { Secteur } from "../api/types";

interface SecteurSidebarProps {
  secteurs: Secteur[];
  selectedId?: string;
  onSelect: (secteurId?: string) => void;
  loading?: boolean;
  allLabel?: string;
  showAllOption?: boolean;
}

export function SecteurSidebar({
  secteurs,
  selectedId,
  onSelect,
  loading,
  allLabel = "Tous les secteurs",
  showAllOption = true,
}: SecteurSidebarProps) {
  return (
    <nav className="dashboard-secteur-nav" aria-label="Filtrer par secteur">
      {loading ? (
        <ul className="space-y-2">
          {Array.from({ length: 6 }).map((_, i) => (
            <li key={i} className="dashboard-secteur-skeleton" />
          ))}
        </ul>
      ) : (
        <ul className="dashboard-secteur-list">
          {showAllOption && (
            <li>
              <button
                type="button"
                onClick={() => onSelect(undefined)}
                className={cn("dashboard-secteur-item", !selectedId && "dashboard-secteur-item-active")}
              >
                <span>{allLabel}</span>
              </button>
            </li>
          )}
          {secteurs.map((secteur) => (
            <li key={secteur.id}>
              <button
                type="button"
                onClick={() => onSelect(secteur.id)}
                className={cn(
                  "dashboard-secteur-item",
                  selectedId === secteur.id && "dashboard-secteur-item-active"
                )}
              >
                <span className="truncate">{secteur.nom}</span>
                <span className="dashboard-secteur-count">{secteur.nb_offres_actives}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </nav>
  );
}
