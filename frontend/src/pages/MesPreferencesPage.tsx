import { FormEvent, useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Briefcase, Globe, Info, Send } from "lucide-react";
import { Button } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { abonnesApi, secteursApi } from "../api";
import type { Secteur } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { cn } from "../lib/cn";
import { PAYS_OPTIONS } from "../lib/format";

import { TogglePill } from "../components/design/TogglePill";

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
      badge="Configuration en cours"
      headerClassName="mt-4 lg:mt-5"
    >
      <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
        <div className="min-h-0 flex-1 overflow-y-auto pb-4">
          <div className="mx-auto max-w-2xl rounded-2xl border border-neutral-100 bg-white p-6 shadow-xl sm:p-8">
            <div className="mb-8 flex gap-3 rounded-xl border border-brand/15 bg-brand/5 px-4 py-3.5">
              <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-brand/15">
                <Info className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
              </div>
              <p className="text-sm leading-relaxed text-neutral-700">
                Vous ne verrez que les offres correspondant à votre sélection. Vous pourrez
                modifier ces choix à tout moment dans Mon compte.
              </p>
            </div>

            <div className="space-y-8">
              <section aria-labelledby="prefs-secteurs-label">
                <div className="mb-4 flex items-center gap-2.5">
                  <div className="flex size-9 items-center justify-center rounded-full bg-brand-muted">
                    <Briefcase className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                  </div>
                  <h2
                    id="prefs-secteurs-label"
                    className="text-sm font-semibold uppercase tracking-wide text-neutral-800"
                  >
                    Secteurs d&apos;activité
                  </h2>
                </div>
                {loading ? (
                  <p className="text-sm text-neutral-500">Chargement…</p>
                ) : secteurs.length === 0 ? (
                  <p className="text-sm text-danger">
                    Aucun secteur disponible. Réessayez dans un instant.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {secteurs.map((s) => (
                      <TogglePill
                        key={s.id}
                        label={s.nom}
                        selected={selectedSecteurs.includes(s.id)}
                        onClick={() => toggleSecteur(s.id)}
                        disabled={loading}
                      />
                    ))}
                  </div>
                )}
              </section>

              <section aria-labelledby="prefs-pays-label">
                <div className="mb-4 flex items-center gap-2.5">
                  <div className="flex size-9 items-center justify-center rounded-full bg-brand-muted">
                    <Globe className="size-4 text-brand" strokeWidth={2} aria-hidden="true" />
                  </div>
                  <h2
                    id="prefs-pays-label"
                    className="text-sm font-semibold uppercase tracking-wide text-neutral-800"
                  >
                    Pays suivis
                  </h2>
                </div>
                <div className="flex flex-wrap gap-2">
                  {PAYS_OPTIONS.map((p) => (
                    <TogglePill
                      key={p}
                      label={p}
                      selected={selectedPays.includes(p)}
                      onClick={() => togglePays(p)}
                      disabled={loading}
                    />
                  ))}
                </div>
              </section>

              {!canSubmit && !loading && (
                <p className="text-sm text-amber-700" role="status">
                  Sélectionnez au moins un secteur <strong>et</strong> un pays pour activer le
                  bouton d&apos;enregistrement.
                </p>
              )}

              {canSubmit && (
                <p className="text-sm text-neutral-600" role="status">
                  {selectedSecteurs.length} secteur
                  {selectedSecteurs.length > 1 ? "s" : ""}, {selectedPays.length} pays sélectionné
                  {selectedPays.length > 1 ? "s" : ""}.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="dashboard-preferences-footer shrink-0 border-t border-neutral-200 bg-surface/95 py-4 backdrop-blur-sm">
          <div className="mx-auto max-w-2xl space-y-3">
            {error && (
              <p className="text-sm text-danger" role="alert">
                {error}
              </p>
            )}
            <Button
              type="submit"
              variant={canSubmit ? "primary" : "secondary"}
              fullWidth
              loading={saving}
              disabled={!canSubmit}
              className={cn(
                canSubmit &&
                  "shadow-lg shadow-brand/20 hover:scale-[1.01] hover:shadow-xl hover:shadow-brand/25"
              )}
            >
              <span className="inline-flex items-center gap-2">
                Enregistrer mon choix
                {canSubmit && <Send className="size-4" strokeWidth={2} aria-hidden="true" />}
              </span>
            </Button>
          </div>
        </div>
      </form>
    </DashboardPage>
  );
}
