import type { ComponentType } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { cn } from "../../lib/cn";
import { SiteBrand } from "../SiteBrand";
import { IconAdmin, IconCalendrier, IconCompte, IconLogout, IconOffres } from "./icons";

interface NavItem {
  to: string;
  label: string;
  icon: ComponentType<{ className?: string }>;
  match?: (path: string) => boolean;
}

interface DashboardSidebarProps {
  isAdmin: boolean;
  onLogout: () => void;
  mobile?: boolean;
  onNavigate?: () => void;
}

export function DashboardSidebar({
  isAdmin,
  onLogout,
  mobile = false,
  onNavigate,
}: DashboardSidebarProps) {
  const { pathname } = useLocation();
  const navigate = useNavigate();

  const clientNav: NavItem[] = [
    { to: "/offres", label: "Offres", icon: IconOffres, match: (p) => p === "/offres" || p.startsWith("/offres/") },
    { to: "/calendrier", label: "Calendrier", icon: IconCalendrier, match: (p) => p === "/calendrier" },
    { to: "/mon-compte", label: "Mon compte", icon: IconCompte, match: (p) => p === "/mon-compte" },
  ];

  const adminNav: NavItem[] = [
    { to: "/admin", label: "Administration", icon: IconAdmin, match: (p) => p.startsWith("/admin") },
  ];

  const navItems = isAdmin ? adminNav : clientNav;

  const isActive = (item: NavItem) =>
    item.match ? item.match(pathname) : pathname === item.to;

  return (
    <aside
      className={cn(
        "flex flex-col",
        mobile ? "h-full" : "dashboard-sidebar hidden w-[260px] shrink-0 lg:flex"
      )}
      aria-label="Navigation principale"
    >
      <div className="dashboard-sidebar-brand px-4 pb-3 pt-6">
        <SiteBrand
          to={isAdmin ? "/admin" : "/offres"}
          size="sidebar"
          className="gap-3.5"
          onNavigate={onNavigate}
        />
      </div>

      <nav className="flex-1 space-y-1 px-3 pt-2">
        {navItems.map((item) => {
          const active = isActive(item);
          const Icon = item.icon;
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={cn(
                "dashboard-nav-item",
                active && "dashboard-nav-item-active"
              )}
            >
              <span
                className={cn(
                  "dashboard-nav-icon",
                  active && "dashboard-nav-icon-active"
                )}
              >
                <Icon className="size-[1.125rem]" />
              </span>
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-neutral-200/60 p-3">
        <button
          type="button"
          onClick={() => {
            onNavigate?.();
            onLogout();
            navigate("/connexion", { replace: true });
          }}
          className="dashboard-nav-item w-full text-neutral-500 hover:text-brand-dark"
        >
          <span className="dashboard-nav-icon">
            <IconLogout className="size-[1.125rem]" />
          </span>
          <span>Déconnexion</span>
        </button>
      </div>
    </aside>
  );
}
