import { FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button, Card } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { abonnesApi, secteursApi } from "../api";
import type { Secteur } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { PAYS_OPTIONS } from "../lib/format";

export function MesPreferencesPage() {
  const { refreshUser, markPreferencesConfigured } = useAuth();
  const navigate = useNavigate();
  const [secteurs, setSecteurs] = useState<Secteur[]>([]);
  const [selectedSecteurs, setSelectedSecteurs] = useState<string[]>([]);
  const [selectedPays, setSelectedPays] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit =
    !loading && selectedSecteurs.length > 0 && selectedPays.length > 0;

  const loadSecteurs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await secteursApi.list();
      setSecteurs(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Impossible de charger les secteurs"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadSecteurs();
  }, [loadSecteurs]);

  const toggleSecteur = (id: string) => {
    setError(null);
    setSelectedSecteurs((prev) =>
      prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]
    );
  };

  const togglePays = (p: string) => {
    setError(null);
    setSelectedPays((prev) =>
      prev.includes(p) ? prev.filter((x) => x !== p) : [...prev, p]
    );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!selectedSecteurs.length || !selectedPays.length) {
      setError("Choisissez au moins un secteur et un pays.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await abonnesApi.save(selectedSecteurs, selectedPays, {
        onboarding: true,
      });
      markPreferencesConfigured();
      await refreshUser();
      navigate("/offres", { replace: true });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Enregistrement impossible");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardPage
      title="Vos préférences"
      subtitle="Choisissez les secteurs et pays qui vous intéressent pour personnaliser votre tableau de bord."
    >
      <form
        onSubmit={handleSubmit}
        className="flex min-h-0 flex-1 flex-col"
      >
        <div className="min-h-0 flex-1 overflow-y-auto pb-4">
          <Card padding="lg" className="mx-auto max-w-2xl">
            <p className="mb-6 text-body text-neutral-600">
              Vous ne verrez que les offres correspondant à votre sélection. Vous pourrez
              modifier ces choix à tout moment dans Mon compte.
            </p>

            <div className="space-y-6">
              <fieldset disabled={loading}>
                <legend className="mb-2 text-body-sm font-medium text-neutral-700">
                  Secteurs d&apos;activité
                </legend>
                {loading ? (
                  <p className="text-body-sm text-neutral-500">Chargement…</p>
                ) : secteurs.length === 0 ? (
                  <p className="text-body-sm text-danger">
                    Aucun secteur disponible. Réessayez dans un instant.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-1">
                    {secteurs.map((s) => (
                      <label key={s.id} className="touch-checkbox-label">
                        <input
                          type="checkbox"
                          checked={selectedSecteurs.includes(s.id)}
                          onChange={() => toggleSecteur(s.id)}
                          className="auth-checkbox"
                        />
                        <span className="text-body-sm">{s.nom}</span>
                      </label>
                    ))}
                  </div>
                )}
              </fieldset>

              <fieldset disabled={loading}>
                <legend className="mb-2 text-body-sm font-medium text-neutral-700">
                  Pays suivis
                </legend>
                <div className="flex flex-wrap gap-1">
                  {PAYS_OPTIONS.map((p) => (
                    <label key={p} className="touch-checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedPays.includes(p)}
                        onChange={() => togglePays(p)}
                        className="auth-checkbox"
                      />
                      <span className="text-body-sm">{p}</span>
                    </label>
                  ))}
                </div>
              </fieldset>

              {!canSubmit && !loading && (
                <p className="text-body-sm text-amber-700" role="status">
                  Sélectionnez au moins un secteur <strong>et</strong> un pays pour
                  activer le bouton bleu.
                </p>
              )}

              {canSubmit && (
                <p className="text-body-sm text-neutral-600" role="status">
                  {selectedSecteurs.length} secteur
                  {selectedSecteurs.length > 1 ? "s" : ""}, {selectedPays.length} pays
                  sélectionné{selectedPays.length > 1 ? "s" : ""}.
                </p>
              )}
            </div>
          </Card>
        </div>

        <div className="dashboard-preferences-footer shrink-0 border-t border-neutral-200 bg-surface/95 py-4 backdrop-blur-sm">
          <div className="mx-auto max-w-2xl space-y-3">
            {error && (
              <p className="text-body-sm text-danger" role="alert">
                {error}
              </p>
            )}
            <Button
              type="submit"
              variant={canSubmit ? "blue" : "secondary"}
              fullWidth
              loading={saving}
              disabled={!canSubmit}
            >
              Enregistrer mon choix
            </Button>
          </div>
        </div>
      </form>
    </DashboardPage>
  );
}
