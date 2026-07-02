import { useEffect, useRef, useState } from "react";
import { AuthStagger } from "./AuthSplitLayout";
import {
  bootstrapGoogle,
  renderGoogleButton,
  resolveGoogleClientId,
  setGoogleCredentialHandler,
} from "../../lib/googleAuth";
import { AppleSignInButton } from "./AppleSignInButton";

interface GoogleSignInButtonProps {
  stagger?: number;
  disabled?: boolean;
  loading?: boolean;
  onSuccess: (credential: string) => void;
  onError?: (message: string) => void;
}

function GoogleIcon() {
  return (
    <svg className="size-5" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="#4285F4"
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
      />
      <path
        fill="#34A853"
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
      />
      <path
        fill="#FBBC05"
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
      />
      <path
        fill="#EA4335"
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
      />
    </svg>
  );
}

type ButtonState = "loading" | "unconfigured" | "ready";

export function GoogleSignInButton({
  stagger = 6,
  disabled = false,
  loading = false,
  onSuccess,
  onError,
}: GoogleSignInButtonProps) {
  const onSuccessRef = useRef(onSuccess);
  const onErrorRef = useRef(onError);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const renderedRef = useRef(false);
  const [clientId, setClientId] = useState<string | null>(null);
  const [state, setState] = useState<ButtonState>("loading");

  onSuccessRef.current = onSuccess;
  onErrorRef.current = onError;

  useEffect(() => {
    setGoogleCredentialHandler((credential) => {
      onSuccessRef.current(credential);
    });
  }, []);

  useEffect(() => {
    if (disabled) {
      return;
    }

    let cancelled = false;

    resolveGoogleClientId()
      .then((id) => {
        if (cancelled) return;
        if (!id) {
          setState("unconfigured");
          return;
        }
        setClientId(id);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState("unconfigured");
        onErrorRef.current?.(
          error instanceof Error
            ? error.message
            : "Impossible de charger l'authentification Google"
        );
      });

    return () => {
      cancelled = true;
    };
  }, [disabled]);

  useEffect(() => {
    if (!clientId || disabled) {
      return;
    }

    let cancelled = false;

    bootstrapGoogle(clientId)
      .then(() => {
        if (cancelled || !containerRef.current) return;
        if (!renderedRef.current) {
          renderGoogleButton(containerRef.current);
          renderedRef.current = true;
        }
        setState("ready");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState("unconfigured");
        onErrorRef.current?.(
          error instanceof Error
            ? error.message
            : "Impossible d'initialiser Google Sign-In"
        );
      });

    return () => {
      cancelled = true;
      renderedRef.current = false;
    };
  }, [clientId, disabled]);

  if (state === "unconfigured") {
    return (
      <AuthStagger index={stagger}>
        <button type="button" className="auth-social-btn" disabled>
          <GoogleIcon />
          Continuer avec Google
        </button>
      </AuthStagger>
    );
  }

  return (
    <AuthStagger index={stagger}>
      <div className="w-full">
        {(state === "loading" || loading) && (
          <button type="button" className="auth-social-btn w-full" disabled>
            <GoogleIcon />
            {loading ? "Connexion Google…" : "Chargement Google…"}
          </button>
        )}
        <div
          ref={containerRef}
          className={`flex min-h-[44px] w-full items-center justify-center ${
            state === "ready" && !loading ? "" : "sr-only"
          }`}
          aria-label="Continuer avec Google"
        />
      </div>
    </AuthStagger>
  );
}

export function AuthSocialButtons({
  stagger = 6,
  googleDisabled = false,
  appleDisabled = false,
  socialLoading = false,
  onGoogleSuccess,
  onGoogleError,
  onAppleSuccess,
  onAppleError,
}: {
  stagger?: number;
  googleDisabled?: boolean;
  appleDisabled?: boolean;
  socialLoading?: boolean;
  onGoogleSuccess: (credential: string) => void;
  onGoogleError?: (message: string) => void;
  onAppleSuccess: (result: { credential: string; prenom?: string; nom?: string }) => void;
  onAppleError?: (message: string) => void;
}) {
  return (
    <div className="space-y-3">
      <GoogleSignInButton
        stagger={stagger}
        disabled={googleDisabled}
        loading={socialLoading}
        onSuccess={onGoogleSuccess}
        onError={onGoogleError}
      />
      <AppleSignInButton
        stagger={stagger}
        disabled={appleDisabled}
        loading={socialLoading}
        onSuccess={onAppleSuccess}
        onError={onAppleError}
      />
    </div>
  );
}
