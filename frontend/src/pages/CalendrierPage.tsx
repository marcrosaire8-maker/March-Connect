import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { LoadingState } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { offresApi } from "../api";
import type { CalendrierJour } from "../api/types";
import { formatDate } from "../lib/format";

const MONTH_NAMES = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

function shiftMonth(year: number, month: number, delta: number) {
  const date = new Date(year, month - 1 + delta, 1);
  return { year: date.getFullYear(), month: date.getMonth() + 1 };
}

export function CalendrierPage() {
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [jours, setJours] = useState<CalendrierJour[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await offresApi.calendrier(year, month);
      setJours(data.jours);
      setTotal(data.total);
    } finally {
      setLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    void load();
  }, [load]);

  const monthLabel = useMemo(
    () => `${MONTH_NAMES[month - 1]} ${year}`,
    [month, year]
  );

  return (
    <DashboardPage
      title="Calendrier des échéances"
      subtitle="Dates limites des offres correspondant à vos critères"
    >
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="dashboard-chip"
            onClick={() => {
              const next = shiftMonth(year, month, -1);
              setYear(next.year);
              setMonth(next.month);
            }}
          >
            ← Mois précédent
          </button>
          <span className="text-base font-semibold text-neutral-900">{monthLabel}</span>
          <button
            type="button"
            className="dashboard-chip"
            onClick={() => {
              const next = shiftMonth(year, month, 1);
              setYear(next.year);
              setMonth(next.month);
            }}
          >
            Mois suivant →
          </button>
        </div>
        <span className="dashboard-live-badge">
          {total} échéance{total > 1 ? "s" : ""}
        </span>
      </div>

      {loading ? (
        <LoadingState variant="spinner" />
      ) : jours.length === 0 ? (
        <p className="text-sm text-neutral-500">Aucune échéance ce mois-ci.</p>
      ) : (
        <div className="space-y-4">
          {jours.map((jour) => (
            <section key={jour.date} className="dashboard-section">
              <h2 className="dashboard-section-title mb-3">
                {formatDate(jour.date)}
              </h2>
              <ul className="space-y-2">
                {jour.offres.map((offre) => (
                  <li key={offre.id} className="dashboard-widget-item">
                    <Link
                      to={`/offres/${offre.id}`}
                      className="block text-sm font-medium text-neutral-900 hover:text-brand"
                    >
                      {offre.titre}
                    </Link>
                    <p className="mt-0.5 text-xs text-neutral-500">
                      {offre.organisme} · {offre.pays}
                    </p>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </DashboardPage>
  );
}
