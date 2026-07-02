import type { ReactNode } from "react";
import { cn } from "../../lib/cn";

interface DashboardPageProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  children: ReactNode;
  /** Pleine hauteur : en-tête fixe, défilement géré par les colonnes enfants (page offres). */
  layout?: "default" | "fill";
}

export function DashboardPage({
  title,
  subtitle,
  action,
  children,
  layout = "default",
}: DashboardPageProps) {
  const isFill = layout === "fill";

  return (
    <div
      className={cn(
        "dashboard-content",
        isFill
          ? "flex min-h-0 flex-1 flex-col lg:overflow-hidden"
          : "flex min-h-0 flex-1 flex-col overflow-y-auto"
      )}
    >
      <header className={cn("dashboard-page-header", isFill && "shrink-0")}>
        <div className="min-w-0">
          <div className="flex items-center gap-2.5">
            <h1 className="dashboard-page-title">{title}</h1>
            <span className="dashboard-live-dot dashboard-live-dot-lg" title="Plateforme active" />
          </div>
          {subtitle && <p className="dashboard-page-subtitle">{subtitle}</p>}
        </div>
        {action}
      </header>
      <div
        className={cn(
          "dashboard-stagger",
          isFill
            ? "flex min-h-0 flex-1 flex-col lg:overflow-hidden"
            : "flex min-h-0 flex-1 flex-col"
        )}
      >
        {children}
      </div>
    </div>
  );
}

interface MetricCardProps {
  label: string;
  value: string | number;
  hint?: string;
  accent?: "green" | "coral" | "gold" | "teal";
  icon?: ReactNode;
}

const accentMap = {
  green: "dashboard-metric-green",
  coral: "dashboard-metric-coral",
  gold: "dashboard-metric-gold",
  teal: "dashboard-metric-teal",
};

export function MetricCard({ label, value, hint, accent = "green", icon }: MetricCardProps) {
  return (
    <div className={cn("dashboard-metric-card", accentMap[accent])}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="dashboard-metric-value">{value}</p>
          <p className="dashboard-metric-label">{label}</p>
          {hint && <p className="dashboard-metric-hint">{hint}</p>}
        </div>
        {icon && <span className="dashboard-metric-icon">{icon}</span>}
      </div>
    </div>
  );
}

export function IconOffers() {
  return (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
    </svg>
  );
}

export function IconSectors() {
  return (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
    </svg>
  );
}

export function IconGlobe() {
  return (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
    </svg>
  );
}

export function IconAccess() {
  return (
    <svg fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-5">
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
    </svg>
  );
}
