import { Navigate, Outlet } from "react-router-dom";
import { LoadingState } from "../LoadingState";
import { useAuth } from "../../context/AuthContext";
import { DashboardSidebar } from "./DashboardSidebar";
import { DashboardTopBar } from "./DashboardTopBar";

export function DashboardShell() {
  const { user, logout, loading } = useAuth();

  if (loading) {
    return (
      <div className="dashboard-page-bg flex min-h-screen items-center justify-center">
        <LoadingState variant="spinner" />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/connexion" replace />;
  }

  const isAdmin = user.role === "admin";

  return (
    <div className="dashboard-page-bg flex h-dvh min-h-screen w-full overflow-hidden">
      <div className="dashboard-shell flex h-full w-full overflow-hidden">
        <DashboardSidebar
          isAdmin={isAdmin}
          onLogout={logout}
        />

        <div className="flex min-w-0 flex-1 flex-col">
          <DashboardTopBar
            userEmail={user.email}
            isAdmin={isAdmin}
            onLogout={logout}
          />

          <main className="dashboard-safe-bottom flex min-h-0 flex-1 flex-col overflow-y-auto px-3 pb-5 sm:px-6 sm:pb-6 lg:overflow-hidden lg:px-8 lg:pb-8 [&>*]:flex [&>*]:min-h-0 [&>*]:flex-1 [&>*]:flex-col">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
