import { Navigate, Route, Routes } from "react-router-dom";
import { LoadingState, ProtectedRoute } from "./components";
import { hasPrefsConfiguredForEmail, hasPrefsConfiguredInSession } from "./api/client";
import { useAuth } from "./context/AuthContext";
import { MainLayout } from "./layouts/MainLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { PublicLayout } from "./layouts/PublicLayout";
import { AdminPage } from "./pages/AdminPage";
import { LoginPage, RegisterPage, VerifyEmailOtpPage, ForgotPasswordPage, VerifyResetOtpPage, ResetPasswordPage, LinkGooglePage, LinkApplePage, ChangePasswordPage } from "./pages/AuthPages";
import { HomePage } from "./pages/HomePage";
import { CalendrierPage } from "./pages/CalendrierPage";
import { OffreDetailPage } from "./pages/OffreDetailPage";
import { MesPreferencesPage } from "./pages/MesPreferencesPage";
import { MonComptePage } from "./pages/MonComptePage";
import { StyleGuidePage } from "./pages/StyleGuidePage";
import { ConditionsUtilisationPage } from "./pages/ConditionsUtilisationPage";
import { LandingPage } from "./pages/LandingPage";
import { AProposPage } from "./pages/AProposPage";
import { ContactPage } from "./pages/ContactPage";
import { PolitiqueConfidentialitePage } from "./pages/PolitiqueConfidentialitePage";
import { MentionsLegalesPage } from "./pages/MentionsLegalesPage";
import { DesabonnementPage } from "./pages/DesabonnementPage";
import { NotFoundPage } from "./pages/NotFoundPage";

function AuthenticatedRedirect() {
  const { isAuthenticated, isAdmin, loading, user, preferencesConfigured } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingState variant="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPage />;
  }

  if (user?.must_change_password) {
    return <Navigate to="/changer-mot-de-passe" replace />;
  }

  const prefsReady =
    preferencesConfigured ||
    hasPrefsConfiguredForEmail(user?.email) ||
    hasPrefsConfiguredInSession();

  if (!isAdmin && user && !prefsReady) {
    return <Navigate to="/mes-preferences" replace />;
  }

  return <Navigate to={isAdmin ? "/admin" : "/offres"} replace />;
}

function GuestOnlyRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAdmin, loading, user, preferencesConfigured } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <LoadingState variant="spinner" />
      </div>
    );
  }

  if (isAuthenticated) {
    if (user?.must_change_password) {
      return <Navigate to="/changer-mot-de-passe" replace />;
    }
    const prefsReady =
      preferencesConfigured ||
      hasPrefsConfiguredForEmail(user?.email) ||
      hasPrefsConfiguredInSession();
    if (!isAdmin && user && !prefsReady) {
      return <Navigate to="/mes-preferences" replace />;
    }
    return <Navigate to={isAdmin ? "/admin" : "/offres"} replace />;
  }

  return <>{children}</>;
}

function DevOnlyStyleGuide() {
  if (!import.meta.env.DEV) {
    return <Navigate to="/connexion" replace />;
  }
  return <StyleGuidePage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/style-guide" element={<DevOnlyStyleGuide />} />

      <Route element={<PublicLayout />}>
        <Route index element={<AuthenticatedRedirect />} />
        <Route path="a-propos" element={<AProposPage />} />
        <Route path="contact" element={<ContactPage />} />
        <Route path="conditions-utilisation" element={<ConditionsUtilisationPage />} />
        <Route path="politique-de-confidentialite" element={<PolitiqueConfidentialitePage />} />
        <Route path="mentions-legales" element={<MentionsLegalesPage />} />
        <Route path="desabonnement" element={<DesabonnementPage />} />
      </Route>

      <Route element={<AuthLayout />}>
        <Route
          path="connexion"
          element={
            <GuestOnlyRoute>
              <LoginPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="inscription"
          element={
            <GuestOnlyRoute>
              <RegisterPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="verification-email"
          element={
            <GuestOnlyRoute>
              <VerifyEmailOtpPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="mot-de-passe-oublie"
          element={
            <GuestOnlyRoute>
              <ForgotPasswordPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="associer-google"
          element={
            <GuestOnlyRoute>
              <LinkGooglePage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="associer-apple"
          element={
            <GuestOnlyRoute>
              <LinkApplePage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="mot-de-passe-verification"
          element={
            <GuestOnlyRoute>
              <VerifyResetOtpPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="reinitialiser-mot-de-passe"
          element={
            <GuestOnlyRoute>
              <ResetPasswordPage />
            </GuestOnlyRoute>
          }
        />
        <Route
          path="mot-de-passe-provisoire"
          element={<Navigate to="/mot-de-passe-oublie" replace />}
        />
        <Route
          path="changer-mot-de-passe"
          element={
            <ProtectedRoute>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route element={<MainLayout />}>
        <Route
          path="mes-preferences"
          element={
            <ProtectedRoute skipPreferencesCheck>
              <MesPreferencesPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="offres/:id"
          element={
            <ProtectedRoute>
              <OffreDetailPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="offres"
          element={
            <ProtectedRoute>
              <HomePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="calendrier"
          element={
            <ProtectedRoute>
              <CalendrierPage />
            </ProtectedRoute>
          }
        />
        <Route path="mes-sites" element={<Navigate to="/offres" replace />} />
        <Route
          path="mon-compte"
          element={
            <ProtectedRoute>
              <MonComptePage />
            </ProtectedRoute>
          }
        />
        <Route
          path="admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
