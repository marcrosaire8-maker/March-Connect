import { useEffect, useState } from "react";
import { SiteBrand } from "../SiteBrand";
import { DashboardSidebar } from "./DashboardSidebar";

interface DashboardTopBarProps {
  userEmail: string;
  isAdmin: boolean;
  onLogout: () => void;
}

function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Bonjour";
  if (hour < 18) return "Bon après-midi";
  return "Bonsoir";
}

function getDisplayName(email: string): string {
  const local = email.split("@")[0] ?? email;
  return local.charAt(0).toUpperCase() + local.slice(1).split(/[._-]/)[0];
}

export function DashboardTopBar({
  userEmail,
  isAdmin,
  onLogout,
}: DashboardTopBarProps) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const initial = userEmail.charAt(0).toUpperCase();

  useEffect(() => {
    if (!mobileOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [mobileOpen]);

  return (
    <>
      <header className="dashboard-topbar dashboard-safe-top flex shrink-0 items-center justify-between gap-3 px-4 py-4 sm:px-6 sm:py-5 lg:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <button
            type="button"
            className="dashboard-icon-btn lg:hidden"
            onClick={() => setMobileOpen(true)}
            aria-label="Ouvrir le menu"
            aria-expanded={mobileOpen}
          >
            <svg className="size-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.75} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          </button>

          <SiteBrand
            to={isAdmin ? "/admin" : "/offres"}
            size="sidebar"
            className="dashboard-topbar-brand gap-3.5 lg:hidden"
          />

          <div className="min-w-0 hidden lg:block">
            <p className="truncate text-sm text-neutral-500">
              {getGreeting()}, {getDisplayName(userEmail)}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          <div className="flex items-center gap-2 rounded-full bg-white/80 py-1 pl-1 pr-3 shadow-sm ring-1 ring-neutral-200/60 sm:gap-2.5 sm:py-1.5 sm:pr-4">
            <span className="flex size-8 shrink-0 items-center justify-center rounded-full bg-brand text-sm font-semibold text-white">
              {initial}
            </span>
            <span className="hidden max-w-[120px] truncate text-sm font-medium text-neutral-700 sm:inline md:max-w-[160px]">
              {userEmail}
            </span>
          </div>
        </div>
      </header>

      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Menu de navigation">
          <button
            type="button"
            className="absolute inset-0 bg-neutral-900/30 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
            aria-label="Fermer le menu"
          />
          <div className="dashboard-mobile-drawer absolute inset-y-0 left-0 flex w-[min(300px,88vw)] flex-col bg-[#faf8f4] shadow-2xl">
            <div className="dashboard-mobile-drawer-header">
              <button
                type="button"
                className="dashboard-icon-btn"
                onClick={() => setMobileOpen(false)}
                aria-label="Fermer le menu"
              >
                <svg className="size-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.75} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <DashboardSidebar
              isAdmin={isAdmin}
              onLogout={onLogout}
              mobile
              onNavigate={() => setMobileOpen(false)}
            />
          </div>
        </div>
      )}
    </>
  );
}
