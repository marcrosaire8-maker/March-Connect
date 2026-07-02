import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { AUTH_PANEL_SRC } from "../../lib/branding";
import { SiteBrand } from "../SiteBrand";

interface AuthSplitLayoutProps {
  formTitle: string;
  panelTitle?: string;
  panelSubtitle: string;
  panelBrand?: boolean;
  children: ReactNode;
  alternateLink?: { label: string; to: string; text: string };
}

export function AuthSplitLayout({
  formTitle,
  panelTitle,
  panelSubtitle,
  panelBrand = false,
  children,
  alternateLink,
}: AuthSplitLayoutProps) {
  return (
    <div className="auth-card auth-card-enter w-full max-w-[920px] overflow-hidden rounded-[20px] sm:rounded-[28px] bg-[#faf8f4]">
      <div className="grid min-h-0 md:min-h-[32rem] md:grid-cols-2">
        <aside className="auth-panel-enter relative hidden overflow-hidden md:flex md:flex-col md:justify-end">
          <img
            src={AUTH_PANEL_SRC}
            alt=""
            className="absolute inset-0 size-full object-cover object-top"
            aria-hidden="true"
          />
          <div
            className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-[#faf8f4]/90 to-transparent"
            aria-hidden="true"
          />
          <div
            className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/55 via-transparent to-transparent"
            aria-hidden="true"
          />
          <div className="relative z-10 p-8 lg:p-10">
            {panelBrand ? (
              <div className="auth-text-enter auth-text-enter-1 space-y-3">
                <h2 className="text-2xl font-bold leading-tight text-white lg:text-4xl">
                  {panelTitle ?? "Bienvenue à"}
                </h2>
                <SiteBrand size="lg" variant="light" />
              </div>
            ) : (
              <h2 className="auth-text-enter auth-text-enter-1 text-2xl font-bold leading-tight text-white lg:text-4xl">
                {panelTitle}
              </h2>
            )}
            <p className="auth-text-enter auth-text-enter-2 mt-3 max-w-xs whitespace-pre-line text-base text-white/90">
              {panelSubtitle}
            </p>
          </div>
        </aside>

        <div className="auth-form-enter flex flex-col justify-center bg-[#faf8f4] px-5 py-8 sm:px-10 sm:py-12 lg:px-12 lg:py-14">
          <div className="auth-mobile-brand relative mb-6 overflow-hidden rounded-2xl md:hidden">
            <img
              src={AUTH_PANEL_SRC}
              alt=""
              className="h-44 w-full object-cover object-top"
              loading="lazy"
              decoding="async"
              aria-hidden="true"
            />
            <div
              className="absolute inset-0 bg-gradient-to-t from-black/55 via-black/10 to-transparent"
              aria-hidden="true"
            />
            <div className="absolute inset-x-0 bottom-0 p-5">
              {panelBrand ? (
                <>
                  <p className="text-lg font-semibold text-white">{panelTitle ?? "Bienvenue à"}</p>
                  <SiteBrand size="md" variant="light" className="mt-2" />
                </>
              ) : (
                <p className="text-lg font-semibold text-white">{panelTitle}</p>
              )}
              <p className="mt-1 whitespace-pre-line text-sm text-white/85">{panelSubtitle}</p>
            </div>
          </div>

          <AuthStagger index={0}>
            <h1 className="mb-6 text-center text-xl font-bold text-neutral-900 sm:mb-8 sm:text-2xl">{formTitle}</h1>
          </AuthStagger>

          {children}

          {alternateLink && (
            <AuthStagger index={7} className="mt-8 text-center text-sm text-neutral-500">
              {alternateLink.text}{" "}
              <Link
                to={alternateLink.to}
                className="font-semibold text-neutral-900 underline decoration-brand/40 underline-offset-4"
              >
                {alternateLink.label}
              </Link>
            </AuthStagger>
          )}
        </div>
      </div>
    </div>
  );
}

const STAGGER_DELAYS: Record<number, string> = {
  0: "0.15s",
  1: "0.22s",
  2: "0.28s",
  3: "0.34s",
  4: "0.4s",
  5: "0.46s",
  6: "0.52s",
  7: "0.58s",
};

export function AuthStagger({
  index,
  className = "",
  children,
}: {
  index: number;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div
      className={`auth-stagger ${className}`}
      style={{ animationDelay: STAGGER_DELAYS[index] ?? "0.3s" }}
    >
      {children}
    </div>
  );
}

export function AuthField({
  id,
  label,
  type = "text",
  value,
  onChange,
  placeholder,
  autoComplete,
  minLength,
  maxLength,
  inputMode,
  required = true,
  stagger = 2,
}: {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  autoComplete?: string;
  minLength?: number;
  maxLength?: number;
  inputMode?: React.HTMLAttributes<HTMLInputElement>["inputMode"];
  required?: boolean;
  stagger?: number;
}) {
  return (
    <AuthStagger index={stagger}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <input
        id={id}
        type={type}
        required={required}
        minLength={minLength}
        maxLength={maxLength}
        inputMode={inputMode}
        autoComplete={autoComplete}
        placeholder={placeholder ?? label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="auth-input w-full"
      />
    </AuthStagger>
  );
}

export function AuthSubmitButton({
  children,
  loading,
  stagger = 5,
}: {
  children: ReactNode;
  loading?: boolean;
  stagger?: number;
}) {
  return (
    <AuthStagger index={stagger}>
      <button
        type="submit"
        disabled={loading}
        className="auth-submit-btn group w-full"
      >
        {loading ? (
          <span className="inline-flex items-center gap-2">
            <span className="size-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            Chargement…
          </span>
        ) : (
          <>
            {children}
            <span className="transition-transform duration-300 group-active:translate-x-1">→</span>
          </>
        )}
      </button>
    </AuthStagger>
  );
}

export function AuthDivider({ stagger = 6 }: { stagger?: number }) {
  return (
    <AuthStagger index={stagger} className="relative my-6 flex items-center">
      <div className="h-px flex-1 bg-neutral-200" />
      <span className="px-4 text-xs text-neutral-400">ou</span>
      <div className="h-px flex-1 bg-neutral-200" />
    </AuthStagger>
  );
}

export function AuthError({ message, stagger = 4 }: { message: string; stagger?: number }) {
  return (
    <AuthStagger index={stagger}>
      <p className="text-sm text-danger" role="alert">
        {message}
      </p>
    </AuthStagger>
  );
}
