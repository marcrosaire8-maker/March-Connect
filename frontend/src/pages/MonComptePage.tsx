import { FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Bell,
  Globe,
  Mail,
  Save,
  Send,
  ShieldAlert,
  Tags,
  Trash2,
  User,
} from "lucide-react";
import { Button } from "../components";
import { ContentCard } from "../components/design/ContentCard";
import { FormField } from "../components/design/FormField";
import { SectionHeading } from "../components/design/SectionHeading";
import { TogglePill } from "../components/design/TogglePill";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { useAuth } from "../context/AuthContext";
import { abonnesApi, secteursApi, notificationsApi } from "../api";
import type { Abonne, Secteur } from "../api/types";
import { pageGradient } from "../lib/design";
import { formatDate, PAYS_OPTIONS } from "../lib/format";
import { NOTIFICATION_INTERVAL_LABEL } from "../lib/branding";
import { fieldInput } from "../lib/design";
import { cn } from "../lib/cn";

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
    <div className={cn("min-h-0 flex-1", pageGradient)}>
      <DashboardPage
        title="Mon compte"
        badge="Mon compte"
        subtitle={user?.email}
        headerClassName="mb-2"
      >
        <div className="mx-auto max-w-4xl space-y-6">
          <ContentCard>
            <SectionHeading icon={User} title="Profil" />
            <p className="text-sm text-neutral-700">{user?.email}</p>
            <p className="mt-1 text-sm text-neutral-500">
              Inscrit le {formatDate(user?.date_inscription)}
            </p>
          </ContentCard>

          <ContentCard variant="accent">
            <form onSubmit={savePreferences} className="space-y-6">
              <SectionHeading
                icon={Tags}
                title="Secteurs et pays suivis"
                description="Ces choix définissent les offres visibles sur votre tableau de bord."
              />

              <div>
                <h3 className="mb-3 text-sm font-semibold text-neutral-800">Secteurs</h3>
                <div className="flex flex-wrap gap-2">
                  {secteurs.map((s) => (
                    <TogglePill
                      key={s.id}
                      label={s.nom}
                      selected={selectedSecteurs.includes(s.id)}
                      onClick={() => toggleSecteur(s.id)}
                    />
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-3 text-sm font-semibold text-neutral-800">Pays</h3>
                <div className="flex flex-wrap gap-2">
                  {PAYS_OPTIONS.map((p) => (
                    <TogglePill
                      key={p}
                      label={p}
                      selected={selectedPays.includes(p)}
                      onClick={() => togglePays(p)}
                    />
                  ))}
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-sm font-semibold text-neutral-800">
                  Mots-clés d&apos;alerte
                </h3>
                <p className="mb-2 text-sm text-neutral-600">
                  Optionnel — affinez les alertes (ex. : mobilier, SONEB, formation).
                </p>
                <input
                  type="text"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  placeholder="mot1, mot2, mot3"
                  className={fieldInput}
                />
              </div>

              <Button type="submit" loading={savingPrefs} className="gap-2">
                <Save className="size-4" strokeWidth={2} aria-hidden="true" />
                Enregistrer les préférences
              </Button>
              {prefsMsg && (
                <p className="text-sm text-neutral-600" role="status">
                  {prefsMsg}
                </p>
              )}
            </form>
          </ContentCard>

          <ContentCard>
            <SectionHeading
              icon={Bell}
              title="Emails d'alerte"
              description={`Alertes RSS automatiques ${NOTIFICATION_INTERVAL_LABEL}, selon vos secteurs, pays et mots-clés.`}
            />

            <Button
              type="button"
              variant="outline"
              loading={previewLoading}
              onClick={() => void testAlerts()}
              className="mb-4 gap-2"
            >
              <Send className="size-4" strokeWidth={2} aria-hidden="true" />
              Tester mes alertes
            </Button>
            {previewMsg && (
              <p className="mb-4 text-sm text-neutral-600" role="status">
                {previewMsg}
              </p>
            )}

            <ul className="mb-4 space-y-2">
              <li className="flex items-center justify-between rounded-xl border border-neutral-100 bg-brand/5 px-3 py-2.5 text-sm">
                <span className="flex items-center gap-2">
                  <Mail className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                  {user?.email}
                </span>
                <span className="text-xs font-medium text-brand">Principal</span>
              </li>
              {(abonne?.emails_supplementaires ?? []).map((addr) => (
                <li
                  key={addr}
                  className="flex items-center justify-between rounded-xl border border-neutral-100 bg-white px-3 py-2.5 text-sm"
                >
                  <span className="flex items-center gap-2">
                    <Globe className="size-4 text-neutral-400" strokeWidth={2} aria-hidden="true" />
                    {addr}
                  </span>
                  <button
                    type="button"
                    disabled={emailLoading}
                    onClick={() => void removeEmail(addr)}
                    className="text-xs font-medium text-danger hover:underline disabled:opacity-50"
                  >
                    Retirer
                  </button>
                </li>
              ))}
            </ul>

            <form onSubmit={(e) => void addEmail(e)} className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="min-w-0 flex-1">
                <FormField
                  id="new-email"
                  label="Ajouter un email"
                  type="email"
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  disabled={emailLoading}
                  icon={Mail}
                />
              </div>
              <Button type="submit" loading={emailLoading}>
                Ajouter
              </Button>
            </form>
            {emailMsg && (
              <p className="mt-2 text-sm text-neutral-600" role="status">
                {emailMsg}
              </p>
            )}
          </ContentCard>

          <ContentCard className="border-danger/20">
            <SectionHeading
              icon={ShieldAlert}
              title="Supprimer mon compte"
              description="Votre compte, vos sites suivis et vos alertes seront supprimés définitivement."
            />
            <form
              onSubmit={(e) => void handleDeleteAccount(e)}
              className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end"
            >
              <div className="min-w-0 flex-1">
                <FormField
                  id="delete-password"
                  label="Confirmez avec votre mot de passe"
                  type="password"
                  required
                  value={deletePassword}
                  onChange={(e) => setDeletePassword(e.target.value)}
                  disabled={deleteLoading}
                />
              </div>
              <Button type="submit" variant="outline" loading={deleteLoading} className="gap-2 border-danger/40 text-danger hover:bg-danger/5">
                <Trash2 className="size-4" strokeWidth={2} aria-hidden="true" />
                Supprimer mon compte
              </Button>
            </form>
            {deleteMsg && (
              <p className="mt-2 text-sm text-danger" role="alert">
                {deleteMsg}
              </p>
            )}
          </ContentCard>
        </div>
      </DashboardPage>
    </div>
  );
}
