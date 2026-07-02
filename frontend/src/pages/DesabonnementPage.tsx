import { FormEvent, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { BellOff, Mail, Send, User } from "lucide-react";
import { abonnesApi } from "../api";
import { ApiError } from "../api/client";
import { Button } from "../components/Button";
import { ContentCard } from "../components/design/ContentCard";
import { FormField } from "../components/design/FormField";
import { PageHeader } from "../components/design/PageHeader";
import { SectionHeading } from "../components/design/SectionHeading";
import { useAuth } from "../context/AuthContext";
import { pageGradient } from "../lib/design";
import { SITE_NAME } from "../lib/branding";

export function DesabonnementPage() {
  const { isAuthenticated, user } = useAuth();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get("email") ?? "");
  const [loading, setLoading] = useState(false);
  const [accountLoading, setAccountLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (user?.email && !email) {
      setEmail(user.email);
    }
  }, [user?.email, email]);

  const handleEmailUnsubscribe = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await abonnesApi.unsubscribeByEmail(email.trim());
      setDone(true);
      setMessage(res.message);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue");
    } finally {
      setLoading(false);
    }
  };

  const handleAccountUnsubscribe = async () => {
    setAccountLoading(true);
    setError(null);
    setMessage(null);
    try {
      const abonne = await abonnesApi.me();
      if (!abonne) {
        setError("Aucun profil d'alerte trouvé pour votre compte.");
        return;
      }
      await abonnesApi.unsubscribe(abonne.id);
      setDone(true);
      setMessage("Vous avez été désinscrit des alertes e-mail.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur est survenue");
    } finally {
      setAccountLoading(false);
    }
  };

  return (
    <div className={pageGradient}>
      <div className="mx-auto max-w-xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <PageHeader
          badge="Désabonnement"
          title="Désabonnement des alertes"
          subtitle={
            <>
              Arrêtez de recevoir les alertes e-mail de {SITE_NAME}. Votre compte reste actif ;
              seules les notifications sont désactivées.
            </>
          }
        />

        <ContentCard variant="elevated" className="space-y-6">
          {done ? (
            <div className="rounded-xl border border-brand-200 bg-brand-50 px-4 py-6 text-center text-sm text-brand-800">
              <p className="font-medium">{message}</p>
              <p className="mt-2 text-brand-700">
                Vous pouvez réactiver les alertes à tout moment depuis{" "}
                <Link to="/mon-compte" className="font-medium underline">
                  Mon compte
                </Link>
                .
              </p>
              <Link
                to="/"
                className="mt-4 inline-block text-sm font-medium text-brand hover:underline"
              >
                Retour à l&apos;accueil
              </Link>
            </div>
          ) : (
            <>
              {isAuthenticated && (
                <div className="rounded-xl border border-neutral-100 bg-brand/5 p-4">
                  <SectionHeading
                    icon={User}
                    title="Compte connecté"
                    description={user?.email}
                  />
                  <Button
                    variant="outline"
                    fullWidth
                    loading={accountLoading}
                    onClick={() => void handleAccountUnsubscribe()}
                    className="gap-2"
                  >
                    <BellOff className="size-4" strokeWidth={2} aria-hidden="true" />
                    Désactiver mes alertes
                  </Button>
                </div>
              )}

              <div>
                <SectionHeading
                  icon={Mail}
                  title={isAuthenticated ? "Ou par adresse e-mail" : "Par adresse e-mail"}
                />
                <form onSubmit={(e) => void handleEmailUnsubscribe(e)} className="space-y-4">
                  <FormField
                    id="unsubscribe-email"
                    label="Adresse e-mail"
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="votre@email.com"
                    icon={Mail}
                  />
                  <Button type="submit" fullWidth loading={loading} className="gap-2">
                    <Send className="size-4" strokeWidth={2} aria-hidden="true" />
                    Se désinscrire des alertes
                  </Button>
                </form>
              </div>

              {error && (
                <p className="text-sm text-danger" role="alert">
                  {error}
                </p>
              )}
            </>
          )}
        </ContentCard>

        <p className="mt-6 text-center text-xs text-neutral-500">
          Pour supprimer définitivement votre compte, rendez-vous dans{" "}
          <Link to="/mon-compte" className="text-brand hover:underline">
            Mon compte
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
