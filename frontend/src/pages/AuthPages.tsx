import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import {
  AuthDivider,
  AuthError,
  AuthField,
  AuthSplitLayout,
  AuthStagger,
  AuthStatusMessage,
  AuthSubmitButton,
} from "../components/auth/AuthSplitLayout";
import { AuthSocialButtons } from "../components/auth/GoogleSignInButton";
import { authApi } from "../api";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";
import { redirectAfterAuth } from "../lib/authRedirect";
import { PASSWORD_HINT, validatePassword } from "../lib/password";

const RESEND_COOLDOWN_SECONDS = 60;
const SUCCESS_REDIRECT_DELAY_MS = 700;

function pause(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms);
  });
}

function useSocialAuthHandler(from = "/offres", mode: "login" | "register" = "login") {
  const { loginWithGoogle, loginWithApple } = useAuth();
  const navigate = useNavigate();
  const [socialLoading, setSocialLoading] = useState(false);
  const [googleError, setGoogleError] = useState<string | null>(null);
  const [appleError, setAppleError] = useState<string | null>(null);
  const [socialStatusMessage, setSocialStatusMessage] = useState<string | null>(null);
  const [socialStatusVariant, setSocialStatusVariant] = useState<"info" | "success">("info");

  const progressLabel =
    mode === "register" ? "Inscription en cours avec Google…" : "Connexion Google en cours…";
  const successLabel =
    mode === "register"
      ? "Inscription réussie avec Google ! Redirection vers votre espace…"
      : "Connexion réussie avec Google ! Redirection vers votre espace…";
  const appleProgressLabel =
    mode === "register" ? "Inscription en cours avec Apple…" : "Connexion Apple en cours…";
  const appleSuccessLabel =
    mode === "register"
      ? "Inscription réussie avec Apple ! Redirection vers votre espace…"
      : "Connexion réussie avec Apple ! Redirection vers votre espace…";

  const handleGoogleSuccess = useCallback(
    async (credential: string) => {
      setSocialLoading(true);
      setGoogleError(null);
      setAppleError(null);
      setSocialStatusVariant("info");
      setSocialStatusMessage(progressLabel);
      try {
        const result = await loginWithGoogle(credential);
        if (result.status === "link_required") {
          setSocialStatusMessage(null);
          navigate("/associer-google", {
            replace: true,
            state: {
              linkToken: result.link_token,
              email: result.email,
              message: result.message,
            },
          });
          return;
        }
        if (result.user) {
          setSocialStatusVariant("success");
          setSocialStatusMessage(successLabel);
          await pause(SUCCESS_REDIRECT_DELAY_MS);
          redirectAfterAuth(result.user, navigate, from);
        }
      } catch (err) {
        setSocialStatusMessage(null);
        setGoogleError(
          err instanceof ApiError
            ? err.message
            : "Erreur lors de l'authentification Google. Réessayez ultérieurement."
        );
      } finally {
        setSocialLoading(false);
      }
    },
    [from, loginWithGoogle, navigate, progressLabel, successLabel]
  );

  const handleAppleSuccess = useCallback(
    async (result: { credential: string; prenom?: string; nom?: string }) => {
      setSocialLoading(true);
      setGoogleError(null);
      setAppleError(null);
      setSocialStatusVariant("info");
      setSocialStatusMessage(appleProgressLabel);
      try {
        const authResult = await loginWithApple(result.credential, {
          prenom: result.prenom,
          nom: result.nom,
        });
        if (authResult.status === "link_required") {
          setSocialStatusMessage(null);
          navigate("/associer-apple", {
            replace: true,
            state: {
              linkToken: authResult.link_token,
              email: authResult.email,
              message: authResult.message,
            },
          });
          return;
        }
        if (authResult.user) {
          setSocialStatusVariant("success");
          setSocialStatusMessage(appleSuccessLabel);
          await pause(SUCCESS_REDIRECT_DELAY_MS);
          redirectAfterAuth(authResult.user, navigate, from);
        }
      } catch (err) {
        setSocialStatusMessage(null);
        setAppleError(
          err instanceof ApiError
            ? err.message
            : "Erreur lors de l'authentification Apple. Réessayez ultérieurement."
        );
      } finally {
        setSocialLoading(false);
      }
    },
    [appleProgressLabel, appleSuccessLabel, from, loginWithApple, navigate]
  );

  return {
    socialLoading,
    socialStatusMessage,
    socialStatusVariant,
    googleError,
    appleError,
    handleGoogleSuccess,
    handleAppleSuccess,
    setGoogleError,
    setAppleError,
  };
}

function PasswordRequirements({ password }: { password: string }) {
  const validation = validatePassword(password);
  if (!password) {
    return (
      <p className="text-xs text-neutral-500">{PASSWORD_HINT}</p>
    );
  }
  if (validation.valid) {
    return <p className="text-xs text-brand-700">Mot de passe conforme.</p>;
  }
  return (
    <ul className="space-y-1 text-xs text-neutral-600">
      {validation.errors.map((error) => (
        <li key={error} className="text-amber-700">
          Manque : {error}
        </li>
      ))}
    </ul>
  );
}

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string })?.from ?? "/offres";
  const successMessage = (location.state as { successMessage?: string })?.successMessage;
  const {
    socialLoading,
    socialStatusMessage,
    socialStatusVariant,
    googleError,
    appleError,
    handleGoogleSuccess,
    handleAppleSuccess,
    setGoogleError,
    setAppleError,
  } = useSocialAuthHandler(from, "login");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusVariant, setStatusVariant] = useState<"info" | "success">("info");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setStatusVariant("info");
    setStatusMessage("Connexion en cours…");
    try {
      const me = await login(email, password);
      setStatusVariant("success");
      setStatusMessage("Connexion réussie ! Redirection vers votre espace…");
      await pause(SUCCESS_REDIRECT_DELAY_MS);
      redirectAfterAuth(me, navigate, from);
    } catch (err) {
      setStatusMessage(null);
      if (err instanceof ApiError && err.status === 403) {
        navigate("/verification-email", {
          replace: true,
          state: { email: email.trim().toLowerCase() },
        });
        return;
      }
      if (err instanceof ApiError && err.status === 401) {
        setError(err.message || "Email ou mot de passe incorrect.");
      } else {
        setError(err instanceof ApiError ? err.message : "Connexion impossible");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthSplitLayout
      badge="Connexion"
      formTitle="Connexion"
      panelBrand
      panelTitle="Bienvenue à"
      panelSubtitle="Accédez à votre espace et consultez les appels d'offres en Afrique de l'Ouest."
      alternateLink={{
        text: "Pas encore de compte ?",
        label: "Créer un compte",
        to: "/inscription",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {successMessage && (
          <AuthStagger index={1}>
            <p className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
              {successMessage}
            </p>
          </AuthStagger>
        )}
        <AuthField
          id="email"
          label="Adresse email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          stagger={2}
        />
        <AuthField
          id="password"
          label="Mot de passe"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          stagger={3}
        />
        <AuthStagger index={4} className="text-right text-sm">
          <Link
            to="/mot-de-passe-oublie"
            className="font-medium text-neutral-600 transition-colors hover:text-neutral-900 hover:underline"
          >
            Mot de passe oublié ?
          </Link>
        </AuthStagger>
        {statusMessage && (
          <AuthStatusMessage variant={statusVariant} message={statusMessage} stagger={4} />
        )}
        {error && <AuthError message={error} stagger={4} />}
        {googleError && <AuthError message={googleError} stagger={4} />}
        {appleError && <AuthError message={appleError} stagger={4} />}
        <AuthSubmitButton
          loading={loading}
          loadingLabel="Connexion en cours…"
          stagger={5}
        >
          Se connecter
        </AuthSubmitButton>
        <AuthDivider stagger={6} />
        {socialStatusMessage && (
          <AuthStatusMessage
            variant={socialStatusVariant}
            message={socialStatusMessage}
            stagger={6}
          />
        )}
        <AuthSocialButtons
          stagger={6}
          googleDisabled={loading || socialLoading}
          appleDisabled={loading || socialLoading}
          socialLoading={socialLoading}
          onGoogleSuccess={handleGoogleSuccess}
          onGoogleError={setGoogleError}
          onAppleSuccess={handleAppleSuccess}
          onAppleError={setAppleError}
        />
      </form>
    </AuthSplitLayout>
  );
}

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const {
    socialLoading,
    socialStatusMessage,
    socialStatusVariant,
    googleError,
    appleError,
    handleGoogleSuccess,
    handleAppleSuccess,
    setGoogleError,
    setAppleError,
  } = useSocialAuthHandler("/mes-preferences", "register");

  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [statusVariant, setStatusVariant] = useState<"info" | "success">("info");

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!acceptTerms) {
      setError("Veuillez accepter les conditions d'utilisation");
      return;
    }
    const validation = validatePassword(password);
    if (!validation.valid) {
      setError(`Mot de passe invalide : ${validation.errors.join(", ")}`);
      return;
    }
    setLoading(true);
    setError(null);
    setStatusVariant("info");
    setStatusMessage("Inscription en cours… Création de votre compte.");
    try {
      const result = await register(email, password, {
        prenom: firstName.trim() || undefined,
        nom: lastName.trim() || undefined,
      });
      navigate("/verification-email", {
        replace: true,
        state: { email: result.email, message: result.message },
      });
    } catch (err) {
      setStatusMessage(null);
      setError(err instanceof ApiError ? err.message : "Inscription impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthSplitLayout
      badge="Inscription"
      formTitle="Inscription"
      panelBrand
      panelTitle="Bienvenue à"
      panelSubtitle="Rejoignez la plateforme et accédez aux appels d'offres selon vos secteurs et pays."
      alternateLink={{
        text: "Déjà inscrit ?",
        label: "Se connecter",
        to: "/connexion",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="first-name"
          label="Prénom"
          autoComplete="given-name"
          value={firstName}
          onChange={setFirstName}
          required={false}
          stagger={2}
        />
        <AuthField
          id="last-name"
          label="Nom"
          autoComplete="family-name"
          value={lastName}
          onChange={setLastName}
          required={false}
          stagger={3}
        />
        <AuthField
          id="reg-email"
          label="Adresse email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          stagger={4}
        />
        <div className="space-y-2">
          <AuthField
            id="reg-password"
            label="Mot de passe"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={setPassword}
            stagger={5}
          />
          <AuthStagger index={5}>
            <PasswordRequirements password={password} />
          </AuthStagger>
        </div>
        <AuthStagger index={5}>
          <div className="flex items-start gap-2.5 text-sm text-neutral-600">
            <input
              id="accept-terms"
              type="checkbox"
              checked={acceptTerms}
              onChange={(e) => setAcceptTerms(e.target.checked)}
              className="auth-checkbox mt-0.5"
            />
            <span>
              <label htmlFor="accept-terms" className="cursor-pointer">
                J&apos;accepte les{" "}
              </label>
              <Link
                to="/conditions-utilisation"
                className="font-medium text-neutral-900 underline decoration-brand/40 underline-offset-4 hover:underline"
              >
                conditions d&apos;utilisation
              </Link>
            </span>
          </div>
        </AuthStagger>
        {statusMessage && (
          <AuthStatusMessage variant={statusVariant} message={statusMessage} stagger={5} />
        )}
        {error && <AuthError message={error} stagger={5} />}
        {googleError && <AuthError message={googleError} stagger={5} />}
        {appleError && <AuthError message={appleError} stagger={5} />}
        <AuthSubmitButton
          loading={loading}
          loadingLabel="Inscription en cours…"
          stagger={6}
        >
          Rejoignez-nous
        </AuthSubmitButton>
        <AuthDivider stagger={7} />
        {socialStatusMessage && (
          <AuthStatusMessage
            variant={socialStatusVariant}
            message={socialStatusMessage}
            stagger={7}
          />
        )}
        <AuthSocialButtons
          stagger={7}
          googleDisabled={loading || socialLoading}
          appleDisabled={loading || socialLoading}
          socialLoading={socialLoading}
          onGoogleSuccess={handleGoogleSuccess}
          onGoogleError={setGoogleError}
          onAppleSuccess={handleAppleSuccess}
          onAppleError={setAppleError}
        />
      </form>
    </AuthSplitLayout>
  );
}

export function VerifyEmailOtpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { verifyEmail } = useAuth();
  const emailFromState = (location.state as { email?: string; message?: string })?.email ?? "";
  const initialMessage = (location.state as { message?: string })?.message ?? null;

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(initialMessage);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (!emailFromState) {
      navigate("/inscription", { replace: true });
    }
  }, [emailFromState, navigate]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(code)) {
      setError("Le code doit contenir exactement 6 chiffres");
      return;
    }
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const me = await verifyEmail(emailFromState, code);
      await pause(SUCCESS_REDIRECT_DELAY_MS);
      redirectAfterAuth(me, navigate, "/mes-preferences");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Vérification impossible");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resendLoading) return;
    setResendLoading(true);
    setError(null);
    setInfo(null);
    try {
      const result = await authApi.resendEmailVerification(emailFromState);
      setInfo(result.message);
      setCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const match = err.message.match(/(\d+)/);
        if (match) {
          setCooldown(Number(match[1]));
        }
      }
      setError(err instanceof ApiError ? err.message : "Renvoi impossible");
    } finally {
      setResendLoading(false);
    }
  };

  if (!emailFromState) {
    return null;
  }

  return (
    <AuthSplitLayout
      badge="Activation"
      formTitle="Vérifiez votre email"
      panelTitle="Consultez votre boîte mail"
      panelSubtitle={`Saisissez le code à 6 chiffres envoyé à ${emailFromState}. Il expire dans 10 minutes.`}
      alternateLink={{
        text: "Déjà un compte ?",
        label: "Se connecter",
        to: "/connexion",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="email-verify-code"
          label="Code de vérification"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={code}
          onChange={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
          placeholder="123456"
          stagger={2}
        />
        {info && (
          <AuthStagger index={3}>
            <p className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
              {info}
            </p>
          </AuthStagger>
        )}
        {error && <AuthError message={error} stagger={3} />}
        <AuthSubmitButton loading={loading} stagger={4}>
          Activer mon compte
        </AuthSubmitButton>
        <AuthStagger index={5}>
          <button
            type="button"
            onClick={handleResend}
            disabled={cooldown > 0 || resendLoading}
            className="w-full text-sm font-medium text-neutral-600 transition-colors hover:text-neutral-900 disabled:cursor-not-allowed disabled:text-neutral-400"
          >
            {resendLoading
              ? "Envoi en cours..."
              : cooldown > 0
                ? `Renvoyer le code (${cooldown}s)`
                : "Renvoyer le code"}
          </button>
        </AuthStagger>
      </form>
    </AuthSplitLayout>
  );
}

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await authApi.forgotPassword(email);
      navigate("/mot-de-passe-verification", {
        replace: true,
        state: { email: email.trim().toLowerCase() },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Envoi impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthSplitLayout
      badge="Récupération"
      formTitle="Mot de passe oublié"
      panelTitle="Récupérez l'accès"
      panelSubtitle="Saisissez votre email. Nous vous enverrons un code temporaire de vérification."
      alternateLink={{
        text: "Vous vous souvenez ?",
        label: "Se connecter",
        to: "/connexion",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="forgot-email"
          label="Adresse email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          stagger={2}
        />
        {error && <AuthError message={error} stagger={3} />}
        <AuthSubmitButton loading={loading} stagger={4}>
          Continuer
        </AuthSubmitButton>
      </form>
    </AuthSplitLayout>
  );
}

export function VerifyResetOtpPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const emailFromState = (location.state as { email?: string })?.email ?? "";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (!emailFromState) {
      navigate("/mot-de-passe-oublie", { replace: true });
    }
  }, [emailFromState, navigate]);

  useEffect(() => {
    if (cooldown <= 0) return;
    const timer = window.setTimeout(() => setCooldown((value) => value - 1), 1000);
    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!/^\d{6}$/.test(code)) {
      setError("Le code doit contenir exactement 6 chiffres");
      return;
    }
    setLoading(true);
    setError(null);
    setInfo(null);
    try {
      const result = await authApi.verifyResetOtp(emailFromState, code);
      navigate("/reinitialiser-mot-de-passe", {
        replace: true,
        state: { email: emailFromState, resetToken: result.reset_token },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Vérification impossible");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (cooldown > 0 || resendLoading) return;
    setResendLoading(true);
    setError(null);
    setInfo(null);
    try {
      const result = await authApi.resendResetOtp(emailFromState);
      setInfo(result.message);
      setCooldown(RESEND_COOLDOWN_SECONDS);
    } catch (err) {
      if (err instanceof ApiError && err.status === 429) {
        const match = err.message.match(/(\d+)/);
        if (match) {
          setCooldown(Number(match[1]));
        }
      }
      setError(err instanceof ApiError ? err.message : "Renvoi impossible");
    } finally {
      setResendLoading(false);
    }
  };

  if (!emailFromState) {
    return null;
  }

  return (
    <AuthSplitLayout
      badge="Vérification"
      formTitle="Vérification du code"
      panelTitle="Consultez votre email"
      panelSubtitle={`Saisissez le code à 6 chiffres envoyé à ${emailFromState}. Il expire dans 10 minutes.`}
      alternateLink={{
        text: "Email incorrect ?",
        label: "Modifier",
        to: "/mot-de-passe-oublie",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="otp-code"
          label="Code temporaire"
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
          value={code}
          onChange={(value) => setCode(value.replace(/\D/g, "").slice(0, 6))}
          placeholder="123456"
          stagger={2}
        />
        {info && (
          <AuthStagger index={3}>
            <p className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
              {info}
            </p>
          </AuthStagger>
        )}
        {error && <AuthError message={error} stagger={3} />}
        <AuthSubmitButton loading={loading} stagger={4}>
          Confirmer
        </AuthSubmitButton>
        <AuthStagger index={5}>
          <button
            type="button"
            onClick={handleResend}
            disabled={cooldown > 0 || resendLoading}
            className="w-full text-sm font-medium text-neutral-600 transition-colors hover:text-neutral-900 disabled:cursor-not-allowed disabled:text-neutral-400"
          >
            {resendLoading
              ? "Envoi en cours..."
              : cooldown > 0
                ? `Renvoyer le code (${cooldown}s)`
                : "Renvoyer le code"}
          </button>
        </AuthStagger>
      </form>
    </AuthSplitLayout>
  );
}

export function ResetPasswordPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = (location.state as { email?: string })?.email ?? "";
  const resetToken = (location.state as { resetToken?: string })?.resetToken ?? "";

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!email || !resetToken) {
      navigate("/mot-de-passe-oublie", { replace: true });
    }
  }, [email, resetToken, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    const validation = validatePassword(password);
    if (!validation.valid) {
      setError(`Mot de passe invalide : ${validation.errors.join(", ")}`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await authApi.resetPassword(resetToken, password, confirm);
      navigate("/connexion", {
        replace: true,
        state: { successMessage: result.message },
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Modification impossible");
    } finally {
      setLoading(false);
    }
  };

  if (!email || !resetToken) {
    return null;
  }

  return (
    <AuthSplitLayout
      badge="Sécurité"
      formTitle="Nouveau mot de passe"
      panelTitle="Sécurisez votre compte"
      panelSubtitle={`Choisissez un nouveau mot de passe pour ${email}.`}
      alternateLink={{
        text: "Besoin d'un nouveau code ?",
        label: "Recommencer",
        to: "/mot-de-passe-oublie",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="reset-password"
          label="Nouveau mot de passe"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
          stagger={2}
        />
        <AuthField
          id="reset-confirm-password"
          label="Confirmer le mot de passe"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={setConfirm}
          stagger={3}
        />
        <AuthStagger index={3}>
          <PasswordRequirements password={password} />
        </AuthStagger>
        {error && <AuthError message={error} stagger={4} />}
        <AuthSubmitButton loading={loading} stagger={5}>
          Enregistrer mon mot de passe
        </AuthSubmitButton>
      </form>
    </AuthSplitLayout>
  );
}

export function LinkGooglePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { completeGoogleLink } = useAuth();

  const linkToken = (location.state as { linkToken?: string })?.linkToken ?? "";
  const email = (location.state as { email?: string })?.email ?? "";
  const infoMessage = (location.state as { message?: string })?.message ?? "";

  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!linkToken || !email) {
      navigate("/connexion", { replace: true });
    }
  }, [email, linkToken, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const me = await completeGoogleLink(linkToken, password);
      redirectAfterAuth(me, navigate);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Association impossible. Réessayez ultérieurement."
      );
    } finally {
      setLoading(false);
    }
  };

  if (!linkToken || !email) {
    return null;
  }

  return (
    <AuthSplitLayout
      badge="Compte Google"
      formTitle="Associer Google"
      panelTitle="Compte existant détecté"
      panelSubtitle={`Un compte existe déjà avec ${email}. Confirmez votre mot de passe pour associer Google.`}
      alternateLink={{
        text: "Retour à",
        label: "la connexion",
        to: "/connexion",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {infoMessage && (
          <AuthStagger index={1}>
            <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {infoMessage}
            </p>
          </AuthStagger>
        )}
        <AuthStagger index={2}>
          <p className="rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-700">
            <span className="font-medium text-neutral-900">Email :</span> {email}
          </p>
        </AuthStagger>
        <AuthField
          id="link-password"
          label="Mot de passe du compte existant"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          stagger={3}
        />
        {error && <AuthError message={error} stagger={4} />}
        <AuthSubmitButton loading={loading} stagger={5}>
          Associer et se connecter
        </AuthSubmitButton>
      </form>
    </AuthSplitLayout>
  );
}

export function LinkApplePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { completeAppleLink } = useAuth();

  const linkToken = (location.state as { linkToken?: string })?.linkToken ?? "";
  const email = (location.state as { email?: string })?.email ?? "";
  const infoMessage = (location.state as { message?: string })?.message ?? "";

  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!linkToken || !email) {
      navigate("/connexion", { replace: true });
    }
  }, [email, linkToken, navigate]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const me = await completeAppleLink(linkToken, password);
      redirectAfterAuth(me, navigate);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Association impossible. Réessayez ultérieurement."
      );
    } finally {
      setLoading(false);
    }
  };

  if (!linkToken || !email) {
    return null;
  }

  return (
    <AuthSplitLayout
      badge="Compte Apple"
      formTitle="Associer Apple"
      panelTitle="Compte existant détecté"
      panelSubtitle={`Un compte existe déjà avec ${email}. Confirmez votre mot de passe pour associer Apple.`}
      alternateLink={{
        text: "Retour à",
        label: "la connexion",
        to: "/connexion",
      }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {infoMessage && (
          <AuthStagger index={1}>
            <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
              {infoMessage}
            </p>
          </AuthStagger>
        )}
        <AuthStagger index={2}>
          <p className="rounded-xl border border-neutral-200 bg-white px-4 py-3 text-sm text-neutral-700">
            <span className="font-medium text-neutral-900">Email :</span> {email}
          </p>
        </AuthStagger>
        <AuthField
          id="link-apple-password"
          label="Mot de passe du compte existant"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          stagger={3}
        />
        {error && <AuthError message={error} stagger={4} />}
        <AuthSubmitButton loading={loading} stagger={5}>
          Associer et se connecter
        </AuthSubmitButton>
      </form>
    </AuthSplitLayout>
  );
}

export function ChangePasswordPage() {
  const navigate = useNavigate();
  const { user, refreshUser, isAdmin } = useAuth();

  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password !== confirm) {
      setError("Les mots de passe ne correspondent pas");
      return;
    }
    const validation = validatePassword(password);
    if (!validation.valid) {
      setError(`Mot de passe invalide : ${validation.errors.join(", ")}`);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await authApi.changePassword(password, confirm);
      await refreshUser();
      navigate(isAdmin ? "/admin" : "/offres", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Modification impossible");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthSplitLayout
      badge="Sécurité"
      formTitle="Nouveau mot de passe"
      panelTitle="Sécurisez votre compte"
      panelSubtitle={
        user?.email
          ? `Choisissez un nouveau mot de passe pour ${user.email}.`
          : "Choisissez un nouveau mot de passe personnel."
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <AuthField
          id="new-password"
          label="Nouveau mot de passe"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
          stagger={2}
        />
        <AuthField
          id="confirm-password"
          label="Confirmer le mot de passe"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={setConfirm}
          stagger={3}
        />
        <AuthStagger index={3}>
          <PasswordRequirements password={password} />
        </AuthStagger>
        {error && <AuthError message={error} stagger={4} />}
        <AuthSubmitButton loading={loading} stagger={5}>
          Enregistrer mon mot de passe
        </AuthSubmitButton>
      </form>
    </AuthSplitLayout>
  );
}
