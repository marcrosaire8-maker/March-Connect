import { useCallback, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
} from "lucide-react";
import { LoadingState } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { offresApi } from "../api";
import type { CalendrierJour, CalendrierOffreItem } from "../api/types";
import { cn } from "../lib/cn";
import { formatDate } from "../lib/format";
import { getSecteurIcon } from "../lib/secteurVisual";

const MONTH_NAMES = [
  "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
  "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
];

const TITLE_CLAMP_THRESHOLD = 110;

function shiftMonth(year: number, month: number, delta: number) {
  const date = new Date(year, month - 1 + delta, 1);
  return { year: date.getFullYear(), month: date.getMonth() + 1 };
}

function ExpandableTitle({ title }: { title: string }) {
  const [expanded, setExpanded] = useState(false);
  const needsClamp = title.length > TITLE_CLAMP_THRESHOLD;

  return (
    <div>
      <p
        className={cn(
          "text-sm font-semibold leading-snug text-neutral-900 sm:text-[0.9375rem]",
          !expanded && needsClamp && "line-clamp-3"
        )}
      >
        {title}
      </p>
      {needsClamp && (
        <button
          type="button"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            setExpanded((v) => !v);
          }}
          className="mt-1 text-xs font-medium text-brand hover:underline"
        >
          {expanded ? "Voir moins" : "Voir plus"}
        </button>
      )}
    </div>
  );
}

function CalendrierOffreCard({ offre }: { offre: CalendrierOffreItem }) {
  const SecteurIcon = getSecteurIcon(offre.secteur_nom);

  return (
    <li>
      <Link
        to={`/offres/${offre.id}`}
        className="group flex gap-3 rounded-xl border border-neutral-100 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-brand/35 hover:shadow-md sm:gap-4 sm:p-5"
      >
        <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-brand-muted transition-colors group-hover:bg-brand/15 sm:size-11">
          <SecteurIcon className="size-5 text-brand" strokeWidth={2} aria-hidden="true" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-start gap-2">
            <span className="inline-flex items-center gap-1 rounded-full border border-brand/20 bg-brand/10 px-2 py-0.5 text-[0.6875rem] font-semibold uppercase tracking-wide text-brand-dark">
              <Clock className="size-3" strokeWidth={2.5} aria-hidden="true" />
              Date limite
            </span>
            {offre.secteur_nom && (
              <span className="inline-flex rounded-full border border-neutral-200 bg-neutral-50 px-2 py-0.5 text-[0.6875rem] font-medium text-neutral-600">
                {offre.secteur_nom}
              </span>
            )}
          </div>

          <ExpandableTitle title={offre.titre} />

          <div className="mt-3 flex flex-wrap gap-2">
            {offre.organisme && (
              <span className="inline-flex max-w-full items-center gap-1.5 rounded-full border border-neutral-200 bg-neutral-50 px-2.5 py-1 text-xs text-neutral-600">
                <MapPin className="size-3 shrink-0 text-brand" strokeWidth={2} aria-hidden="true" />
                <span className="truncate">{offre.organisme}</span>
              </span>
            )}
            {offre.pays && (
              <span className="inline-flex items-center rounded-full border border-brand/15 bg-brand-muted px-2.5 py-1 text-xs font-medium text-brand-dark">
                {offre.pays}
              </span>
            )}
          </div>

          <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-brand opacity-0 transition-opacity group-hover:opacity-100">
            Voir le détail
            <ChevronRight className="size-3.5" strokeWidth={2.5} aria-hidden="true" />
          </span>
        </div>
      </Link>
    </li>
  );
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

  const goToPreviousMonth = () => {
    const next = shiftMonth(year, month, -1);
    setYear(next.year);
    setMonth(next.month);
  };

  const goToNextMonth = () => {
    const next = shiftMonth(year, month, 1);
    setYear(next.year);
    setMonth(next.month);
  };

  return (
    <div className="min-h-0 flex-1 bg-gradient-to-b from-white via-surface to-brand-muted/40">
      <DashboardPage
        title="Calendrier des échéances"
        subtitle="Dates limites des offres correspondant à vos critères"
        badge="Échéances du mois"
        headerClassName="mb-0"
      >
        <div className="mt-6 rounded-2xl border border-neutral-100 bg-white p-4 shadow-md sm:p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex flex-wrap items-center gap-2 sm:gap-3">
              <button
                type="button"
                className="dashboard-chip inline-flex items-center gap-1.5 hover:border-brand/30 hover:bg-brand-muted hover:text-brand-dark"
                onClick={goToPreviousMonth}
              >
                <ChevronLeft className="size-4" strokeWidth={2} aria-hidden="true" />
                Mois précédent
              </button>
              <span className="inline-flex items-center gap-2 px-2 text-base font-bold text-neutral-900">
                <CalendarDays className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                {monthLabel}
              </span>
              <button
                type="button"
                className="dashboard-chip inline-flex items-center gap-1.5 hover:border-brand/30 hover:bg-brand-muted hover:text-brand-dark"
                onClick={goToNextMonth}
              >
                Mois suivant
                <ChevronRight className="size-4" strokeWidth={2} aria-hidden="true" />
              </button>
            </div>
            <span className="inline-flex rounded-full border border-brand/20 bg-brand-muted px-3.5 py-1.5 text-sm font-semibold text-brand-dark">
              {total} échéance{total > 1 ? "s" : ""}
            </span>
          </div>
        </div>

        <div className="mt-8">
          {loading ? (
            <LoadingState variant="spinner" />
          ) : jours.length === 0 ? (
            <div className="rounded-2xl border border-neutral-100 bg-white px-6 py-12 text-center shadow-sm">
              <CalendarDays className="mx-auto size-10 text-brand/40" strokeWidth={1.5} aria-hidden="true" />
              <p className="mt-3 text-sm text-neutral-500">Aucune échéance ce mois-ci.</p>
            </div>
          ) : (
            <div className="space-y-8">
              {jours.map((jour) => (
                <section
                  key={jour.date}
                  className="rounded-xl border border-neutral-100 border-l-4 border-l-brand bg-white/70 p-4 shadow-sm sm:p-5"
                >
                  <div className="mb-4 flex items-center gap-2.5 border-b border-neutral-100 pb-3">
                    <div className="flex size-8 items-center justify-center rounded-full bg-brand-muted">
                      <Clock className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                    </div>
                    <h2 className="text-base font-bold text-neutral-900">
                      {formatDate(jour.date)}
                    </h2>
                    <span className="ml-auto rounded-full bg-neutral-100 px-2 py-0.5 text-xs font-medium text-neutral-600">
                      {jour.offres.length} offre{jour.offres.length > 1 ? "s" : ""}
                    </span>
                  </div>
                  <ul className="space-y-3">
                    {jour.offres.map((offre) => (
                      <CalendrierOffreCard key={offre.id} offre={offre} />
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          )}
        </div>
      </DashboardPage>
    </div>
  );
}
