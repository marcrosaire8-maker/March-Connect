import { FormEvent, useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "./Button";
import { LoadingState } from "./LoadingState";
import { abonnesApi, notificationsApi } from "../api";
import type { Abonne } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { NOTIFICATION_INTERVAL_LABEL } from "../lib/branding";

export function NotificationEmailsPanel({ embedded = false }: { embedded?: boolean }) {
  const { user, loading: authLoading } = useAuth();
  const [abonne, setAbonne] = useState<Abonne | null>(null);
  const [loading, setLoading] = useState(true);
  const [newEmail, setNewEmail] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAbonne(await abonnesApi.me());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    void load();
  }, [authLoading, load]);

  const addEmail = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = newEmail.trim();
    if (!trimmed) return;
    setEmailLoading(true);
    setMessage(null);
    try {
      setAbonne(await abonnesApi.addEmail(trimmed));
      setNewEmail("");
      setMessage("Email ajouté.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur");
    } finally {
      setEmailLoading(false);
    }
  };

  const removeEmail = async (email: string) => {
    setEmailLoading(true);
    setMessage(null);
    try {
      setAbonne(await abonnesApi.removeEmail(email));
      setMessage("Email retiré.");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur");
    } finally {
      setEmailLoading(false);
    }
  };

  const testAlerts = async () => {
    setPreviewLoading(true);
    setMessage(null);
    try {
      const result = await notificationsApi.previewMe();
      if (result.nb_emails_envoyes > 0) {
        setMessage(`Aperçu envoyé (${result.nb_offres} offre${result.nb_offres > 1 ? "s" : ""}).`);
      } else {
        setMessage("Aucune offre pour l'aperçu actuellement.");
      }
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur test alertes");
    } finally {
      setPreviewLoading(false);
    }
  };

  const content = (
    <>
      {!embedded && (
        <>
          <h2 className="mb-1 text-base font-semibold text-neutral-900">Alertes email</h2>
          <p className="mb-4 text-sm text-neutral-500">
            Alertes automatiques {NOTIFICATION_INTERVAL_LABEL} : offres encore ouvertes selon vos
            secteurs et pays (Mon compte).
          </p>
        </>
      )}

      {loading ? (
        <LoadingState variant="spinner" />
      ) : (
        <>
          <ul className={embedded ? "mb-3 space-y-1.5" : "mb-4 space-y-2"}>
            <li className="dashboard-widget-email">
              <span className="break-all text-sm">{user?.email}</span>
              <span className="text-xs text-neutral-500">Principal</span>
            </li>
            {(abonne?.emails_supplementaires ?? []).map((addr) => (
              <li key={addr} className="dashboard-widget-email flex items-start justify-between gap-2">
                <span className="min-w-0 break-all text-sm">{addr}</span>
                <button
                  type="button"
                  disabled={emailLoading}
                  onClick={() => removeEmail(addr)}
                  className="shrink-0 text-xs font-medium text-danger hover:underline disabled:opacity-50"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>

          <Button
            type="button"
            variant="secondary"
            fullWidth
            loading={previewLoading}
            onClick={() => void testAlerts()}
            className="mb-2"
          >
            Tester mes alertes
          </Button>

          <form onSubmit={addEmail} className="space-y-2">
            {!embedded && (
              <label htmlFor="notif-email" className="block text-sm font-medium text-neutral-700">
                Ajouter un email
              </label>
            )}
            <input
              id="notif-email"
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="email@entreprise.com"
              className="dashboard-input"
              disabled={emailLoading}
            />
            <Button type="submit" variant="primary" fullWidth loading={emailLoading}>
              Ajouter
            </Button>
          </form>

          {message && (
            <p className="mt-2 text-xs text-neutral-600" role="status">
              {message}
            </p>
          )}

          {!embedded && (
            <p className="mt-3 text-caption text-neutral-500">
              Jusqu&apos;à 5 emails supplémentaires. Configurez secteurs et pays dans{" "}
              <Link to="/mon-compte" className="text-brand hover:underline">
                Mon compte
              </Link>
              .
            </p>
          )}
        </>
      )}
    </>
  );

  if (embedded) return content;

  return (
    <aside className="xl:sticky xl:top-6 xl:self-start">
      <div className="dashboard-filter-card">{content}</div>
    </aside>
  );
}
