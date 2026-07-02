import { Outlet, useLocation } from "react-router-dom";
import { cn } from "../lib/cn";
import { PublicFooter } from "../components/PublicFooter";
import { PublicHeader } from "../components/PublicHeader";

export function PublicLayout() {
  const { pathname } = useLocation();
  const isLanding = pathname === "/";

  return (
    <div
      className={cn(
        "flex min-h-dvh min-h-screen flex-col",
        !isLanding && "bg-gradient-to-b from-white via-surface to-brand-muted/40"
      )}
    >
      {!isLanding && <PublicHeader />}
      <main className="flex-1">
        <Outlet />
      </main>
      <PublicFooter />
    </div>
  );
}
