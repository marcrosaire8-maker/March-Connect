import { Navigate, useLocation } from "react-router-dom";
import { LoadingState } from "../components";
import { hasPrefsConfiguredForEmail, hasPrefsConfiguredInSession } from "../api/client";
import { useAuth } from "../context/AuthContext";

interface ProtectedRouteProps {
  children: React.ReactNode;
  requireAdmin?: boolean;
  skipPreferencesCheck?: boolean;
}

export function ProtectedRoute({
  children,
  requireAdmin = false,
  skipPreferencesCheck = false,
}: ProtectedRouteProps) {
  const { isAuthenticated, isAdmin, loading, user, preferencesConfigured } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingState variant="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/connexion" state={{ from: location.pathname }} replace />;
  }

  if (user?.must_change_password && location.pathname !== "/changer-mot-de-passe") {
    return <Navigate to="/changer-mot-de-passe" replace />;
  }

  const prefsReady =
    preferencesConfigured ||
    hasPrefsConfiguredForEmail(user?.email) ||
    hasPrefsConfiguredInSession();

  if (
    !skipPreferencesCheck &&
    !requireAdmin &&
    !isAdmin &&
    user &&
    !prefsReady &&
    location.pathname !== "/mes-preferences"
  ) {
    return <Navigate to="/mes-preferences" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/offres" replace />;
  }

  return <>{children}</>;
}
