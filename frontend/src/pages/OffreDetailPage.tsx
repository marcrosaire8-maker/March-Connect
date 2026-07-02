import { useCallback, useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button, LoadingState, OffreCard } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { favorisApi, offresApi } from "../api";
import type { Offre } from "../api/types";
import { formatDate } from "../lib/format";

export function OffreDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [offre, setOffre] = useState<Offre | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFavori, setIsFavori] = useState(false);
  const [favLoading, setFavLoading] = useState(false);

  const load = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const [detail, favoris] = await Promise.all([
        offresApi.get(id),
        favorisApi.list(),
      ]);
      setOffre(detail);
      setIsFavori(favoris.includes(id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Offre introuvable");
      setOffre(null);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const toggleFavori = async () => {
    if (!offre) return;
    setFavLoading(true);
    try {
      if (isFavori) {
        await favorisApi.remove(offre.id);
        setIsFavori(false);
      } else {
        await favorisApi.add(offre.id);
        setIsFavori(true);
      }
    } finally {
      setFavLoading(false);
    }
  };

  if (loading) {
    return (
      <DashboardPage title="Détail de l'offre">
        <LoadingState variant="spinner" />
      </DashboardPage>
    );
  }

  if (error || !offre) {
    return (
      <DashboardPage title="Offre introuvable">
        <p className="text-body-sm text-danger">{error ?? "Cette offre n'existe pas."}</p>
        <Button variant="secondary" className="mt-4" onClick={() => navigate("/offres")}>
          Retour aux offres
        </Button>
      </DashboardPage>
    );
  }

  return (
    <DashboardPage
      title="Détail de l'offre"
      subtitle={`${offre.organisme} · ${offre.pays}`}
    >
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Link to="/offres" className="text-sm font-medium text-brand hover:underline">
          ← Retour aux offres
        </Link>
        <Button
          variant={isFavori ? "primary" : "outline"}
          loading={favLoading}
          onClick={() => void toggleFavori()}
        >
          {isFavori ? "Retirer des favoris" : "Ajouter aux favoris"}
        </Button>
      </div>

      <OffreCard
        offreId={offre.id}
        titre={offre.titre}
        organisme={offre.organisme}
        description={offre.description}
        contact={offre.contact}
        dateLimite={offre.date_limite ? formatDate(offre.date_limite) : undefined}
        lienSource={offre.lien_source}
        showDetailLink={false}
      />

      {offre.description && (
        <section className="dashboard-section mt-6">
          <h2 className="dashboard-section-title mb-3">Description</h2>
          <p className="whitespace-pre-wrap text-sm leading-relaxed text-neutral-700">
            {offre.description}
          </p>
        </section>
      )}

      {offre.montant_estime && (
        <p className="mt-4 text-sm text-neutral-600">
          <strong>Montant estimé :</strong> {offre.montant_estime}
        </p>
      )}
    </DashboardPage>
  );
}
