import { FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { useAuth } from "../context/AuthContext";
import { abonnesApi, secteursApi, notificationsApi } from "../api";
import type { Abonne, Secteur } from "../api/types";
import { formatDate, PAYS_OPTIONS } from "../lib/format";
import { NOTIFICATION_INTERVAL_LABEL } from "../lib/branding";

export function MonComptePage() {
  const { user, loading: authLoading, deleteAccount, refreshUser, markPreferencesConfigured } = useAuth();
  const navigate = useNavigate();
  const [secteurs, setSecteurs] = useState<Secteur[]>([]);
  const [abonne, setAbonne] = useState<Abonne | null>(null);
  const [selectedSecteurs, setSelectedSecteurs] = useState<string[]>([]);
  const [selectedPays, setSelectedPays] = useState<string[]>([]);
  const [keywords, setKeywords] = useState("");
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsMsg, setPrefsMsg] = useState<string | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewMsg, setPreviewMsg] = useState<string | null>(null);
  const [newEmail, setNewEmail] = useState("");
  const [emailMsg, setEmailMsg] = useState<string | null>(null);
  const [emailLoading, setEmailLoading] = useState(false);
  const [deletePassword, setDeletePassword] = useState("");
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteMsg, setDeleteMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    const [secteursData, abonneData] = await Promise.all([
      secteursApi.list(),
      abonnesApi.me(),
    ]);
    setSecteurs(secteursData);
    if (abonneData) {
      setAbonne(abonneData);
      setSelectedSecteurs(abonneData.secteurs_suivis);
      setSelectedPays(abonneData.pays_suivis);
      setKeywords((abonneData.mots_cles_alertes ?? []).join(", "));
    }
  }, []);

  useEffect(() => {
    if (authLoading) return;
    void loadData();
  }, [authLoading, loadData]);

  const toggleSecteur = (id: string) => {
    setSelectedSecteurs((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const togglePays = (p: string) => {
    setSelectedPays((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const savePreferences = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedSecteurs.length || !selectedPays.length) {
      setPrefsMsg("Choisissez au moins un secteur et un pays.");
      return;
    }
    setSavingPrefs(true);
    setPrefsMsg(null);
    try {
      const saved = await abonnesApi.save(selectedSecteurs, selectedPays, {
        mots_cles_alertes: keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
      });
      setAbonne(saved);
      markPreferencesConfigured();
      await refreshUser();
      setPrefsMsg("Préférences enregistrées.");
    } catch (err) {
      setPrefsMsg(err instanceof Error ? err.message : "Erreur");
    } finally {
      setSavingPrefs(false);
    }
  };

  const addEmail = async (e: FormEvent) => {
    e.preventDefault();
    const trimmed = newEmail.trim();
    if (!trimmed) return;
    setEmailLoading(true);
    setEmailMsg(null);
    try {
      const saved = await abonnesApi.addEmail(trimmed);
      setAbonne(saved);
      setNewEmail("");
      setEmailMsg("Email ajouté.");
    } catch (err) {
      setEmailMsg(err instanceof Error ? err.message : "Erreur");
    } finally {
      setEmailLoading(false);
    }
  };

  const removeEmail = async (email: string) => {
    setEmailLoading(true);
    setEmailMsg(null);
    try {
      const saved = await abonnesApi.removeEmail(email);
      setAbonne(saved);
      setEmailMsg("Email retiré.");
    } catch (err) {
      setEmailMsg(err instanceof Error ? err.message : "Erreur");
    } finally {
      setEmailLoading(false);
    }
  };

  const testAlerts = async () => {
    setPreviewLoading(true);
    setPreviewMsg(null);
    try {
      const result = await notificationsApi.previewMe();
      if (result.nb_emails_envoyes > 0) {
        setPreviewMsg(
          `Aperçu envoyé (${result.nb_offres} offre${result.nb_offres > 1 ? "s" : ""}).`
        );
      } else {
        setPreviewMsg("Aucune offre à envoyer pour l'aperçu actuellement.");
      }
    } catch (err) {
      setPreviewMsg(err instanceof Error ? err.message : "Erreur lors du test");
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleDeleteAccount = async (e: FormEvent) => {
    e.preventDefault();
    if (
      !window.confirm(
        "Supprimer définitivement votre compte et toutes vos données ? Cette action est irréversible."
      )
    ) {
      return;
    }
    setDeleteLoading(true);
    setDeleteMsg(null);
    try {
      await deleteAccount(deletePassword);
      navigate("/connexion", { replace: true });
    } catch (err) {
      setDeleteMsg(err instanceof Error ? err.message : "Suppression impossible");
    } finally {
      setDeleteLoading(false);
    }
  };

  return (
    <DashboardPage
      title="Mon compte"
      subtitle={user?.email}
    >
      <Card className="mb-8">
        <h2 className="mb-2 text-h3">Profil</h2>
        <p className="text-body text-neutral-700">{user?.email}</p>
        <p className="mt-1 text-body-sm text-neutral-500">
          Inscrit le {formatDate(user?.date_inscription)}
        </p>
      </Card>

      <Card className="mb-8 border-danger/30" padding="lg">
        <h2 className="mb-2 text-h3 text-danger">Supprimer mon compte</h2>
        <p className="mb-4 text-body-sm text-neutral-600">
          Votre compte, vos sites suivis et vos alertes seront supprimés définitivement.
        </p>
        <form onSubmit={handleDeleteAccount} className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
          <div className="min-w-0 flex-1">
            <label htmlFor="delete-password" className="mb-1 block text-body-sm font-medium">
              Confirmez avec votre mot de passe
            </label>
            <input
              id="delete-password"
              type="password"
              required
              value={deletePassword}
              onChange={(e) => setDeletePassword(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-body"
              disabled={deleteLoading}
            />
          </div>
          <Button type="submit" variant="outline" loading={deleteLoading}>
            Supprimer mon compte
          </Button>
        </form>
        {deleteMsg && (
          <p className="mt-2 text-body-sm text-danger" role="alert">
            {deleteMsg}
          </p>
        )}
      </Card>

      <Card className="mb-8" padding="lg">
        <h2 className="mb-2 text-h2">Secteurs et pays suivis</h2>
        <p className="mb-4 text-body-sm text-neutral-600">
          Ces choix définissent les offres visibles sur votre tableau de bord.
        </p>

        <form onSubmit={savePreferences} className="space-y-6">
          <div>
            <h3 className="mb-3 text-body font-semibold">Secteurs</h3>
            <div className="flex flex-wrap gap-2">
              {secteurs.map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => toggleSecteur(s.id)}
                  className={`rounded-full border px-4 py-2 text-sm transition-colors ${
                    selectedSecteurs.includes(s.id)
                      ? "border-brand bg-brand text-white"
                      : "border-neutral-300 bg-white text-neutral-700 hover:border-neutral-400"
                  }`}
                >
                  {s.nom}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="mb-3 text-body font-semibold">Pays</h3>
            <div className="flex flex-wrap gap-2">
              {PAYS_OPTIONS.map((p) => (
                <button
                  key={p}
                  type="button"
                  onClick={() => togglePays(p)}
                  className={`rounded-full border px-4 py-2 text-sm transition-colors ${
                    selectedPays.includes(p)
                      ? "border-brand bg-brand text-white"
                      : "border-neutral-300 bg-white text-neutral-700 hover:border-neutral-400"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-body font-semibold">Mots-clés d&apos;alerte</h3>
            <p className="mb-2 text-body-sm text-neutral-600">
              Optionnel — affinez les alertes (ex. : mobilier, SONEB, formation).
            </p>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="mot1, mot2, mot3"
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-body"
            />
          </div>

          <Button type="submit" loading={savingPrefs}>
            Enregistrer les préférences
          </Button>
          {prefsMsg && (
            <p className="text-body-sm text-neutral-600" role="status">
              {prefsMsg}
            </p>
          )}
        </form>
      </Card>

      <Card padding="lg">
        <h2 className="mb-2 text-h2">Emails d&apos;alerte</h2>
        <p className="mb-4 text-body-sm text-neutral-600">
          Alertes RSS automatiques {NOTIFICATION_INTERVAL_LABEL}, selon vos secteurs, pays et mots-clés.
        </p>

        <Button
          type="button"
          variant="secondary"
          loading={previewLoading}
          onClick={() => void testAlerts()}
          className="mb-4"
        >
          Tester mes alertes
        </Button>
        {previewMsg && (
          <p className="mb-4 text-body-sm text-neutral-600" role="status">
            {previewMsg}
          </p>
        )}

        <ul className="mb-4 space-y-2">
          <li className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2 text-sm">
            <span>{user?.email}</span>
            <span className="text-xs text-neutral-500">Principal</span>
          </li>
          {(abonne?.emails_supplementaires ?? []).map((addr) => (
            <li
              key={addr}
              className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2 text-sm"
            >
              <span>{addr}</span>
              <button
                type="button"
                disabled={emailLoading}
                onClick={() => removeEmail(addr)}
                className="text-xs font-medium text-danger hover:underline disabled:opacity-50"
              >
                Retirer
              </button>
            </li>
          ))}
        </ul>

        <form onSubmit={addEmail} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <div className="min-w-0 flex-1">
            <label htmlFor="new-email" className="mb-1 block text-body-sm font-medium">
              Ajouter un email
            </label>
            <input
              id="new-email"
              type="email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              className="w-full rounded-lg border border-neutral-300 px-3 py-2 text-body"
              disabled={emailLoading}
            />
          </div>
          <Button type="submit" loading={emailLoading}>
            Ajouter
          </Button>
        </form>
        {emailMsg && (
          <p className="mt-2 text-body-sm text-neutral-600" role="status">
            {emailMsg}
          </p>
        )}
      </Card>
    </DashboardPage>
  );
}
