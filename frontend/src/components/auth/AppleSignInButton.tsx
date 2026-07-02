import { useEffect, useState } from "react";
import { AuthStagger } from "./AuthSplitLayout";
import { isAppleAuthConfigured, resolveAppleConfig, signInWithApple } from "../../lib/appleAuth";

interface AppleSignInButtonProps {
  stagger?: number;
  disabled?: boolean;
  loading?: boolean;
  onSuccess: (result: { credential: string; prenom?: string; nom?: string }) => void;
  onError?: (message: string) => void;
}

function AppleIcon() {
  return (
    <svg className="size-5 fill-current" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M17.05 20.28c-.98.95-2.05.88-3.08.4-1.09-.5-2.08-.48-3.24 0-1.44.62-2.2.44-3.06-.4C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
    </svg>
  );
}

type ButtonState = "loading" | "unconfigured" | "ready";

export function AppleSignInButton({
  stagger = 6,
  disabled = false,
  loading = false,
  onSuccess,
  onError,
}: AppleSignInButtonProps) {
  const [state, setState] = useState<ButtonState>(
    isAppleAuthConfigured() ? "ready" : "loading"
  );
  const [signingIn, setSigningIn] = useState(false);

  useEffect(() => {
    if (disabled || isAppleAuthConfigured()) {
      return;
    }

    let cancelled = false;

    resolveAppleConfig()
      .then((config) => {
        if (cancelled) return;
        setState(config ? "ready" : "unconfigured");
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState("unconfigured");
        onError?.(
          error instanceof Error
            ? error.message
            : "Impossible de charger l'authentification Apple"
        );
      });

    return () => {
      cancelled = true;
    };
  }, [disabled, onError]);

  const handleClick = async () => {
    if (disabled || loading || signingIn || state !== "ready") {
      return;
    }

    setSigningIn(true);
    try {
      const result = await signInWithApple();
      onSuccess(result);
    } catch (error: unknown) {
      const message =
        error instanceof Error && error.message
          ? error.message
          : "Erreur lors de l'authentification Apple. Réessayez ultérieurement.";
      if (!message.toLowerCase().includes("popup closed")) {
        onError?.(message);
      }
    } finally {
      setSigningIn(false);
    }
  };

  if (state === "unconfigured") {
    return (
      <AuthStagger index={stagger}>
        <button type="button" className="auth-social-btn auth-social-btn-dark" disabled>
          <AppleIcon />
          Continuer avec Apple
        </button>
      </AuthStagger>
    );
  }

  return (
    <AuthStagger index={stagger}>
      <button
        type="button"
        className="auth-social-btn auth-social-btn-dark w-full"
        onClick={handleClick}
        disabled={disabled || loading || signingIn || state === "loading"}
      >
        <AppleIcon />
        {signingIn
          ? "Connexion Apple…"
          : state === "loading"
            ? "Chargement Apple…"
            : "Continuer avec Apple"}
      </button>
    </AuthStagger>
  );
}
