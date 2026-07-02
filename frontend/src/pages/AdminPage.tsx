import { useCallback, useEffect, useMemo, useState } from "react";
import { Badge, Button, Card, LoadingState } from "../components";
import { DashboardPage } from "../components/dashboard/DashboardPage";
import { adminApi } from "../api";
import { useAuth } from "../context/AuthContext";
import type {
  AdminUtilisateur,
  LogNotification,
  LogScraping,
  Source,
} from "../api/types";
import { formatDateTime } from "../lib/format";

type Tab = "sources" | "scraping" | "notifications" | "users";

function StatusBadge({ statut }: { statut: string }) {
  const variant =
    statut === "succes" || statut === "actif"
      ? "actif"
      : statut === "echec" || statut === "expire"
        ? "inactif"
        : "neutral";
  return <Badge variant={variant}>{statut}</Badge>;
}

export function AdminPage() {
  const { user: currentUser } = useAuth();
  const [tab, setTab] = useState<Tab>("sources");
  const [sources, setSources] = useState<Source[]>([]);
  const [logs, setLogs] = useState<LogScraping[]>([]);
  const [notifLogs, setNotifLogs] = useState<LogNotification[]>([]);
  const [users, setUsers] = useState<AdminUtilisateur[]>([]);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [showAddSource, setShowAddSource] = useState(false);
  const [creatingSource, setCreatingSource] = useState(false);
  const [newSource, setNewSource] = useState({
    nom: "",
    pays: "",
    url_base: "",
    type_scraping: "html" as "html" | "api" | "rss",
  });
  const [deletingUserId, setDeletingUserId] = useState<string | null>(null);

  const lastLogBySource = useMemo(() => {
    const map: Record<string, LogScraping> = {};
    logs.forEach((log) => {
      if (!map[log.source_id]) map[log.source_id] = log;
    });
    return map;
  }, [logs]);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [src, scrLogs, nLogs, usrs] = await Promise.all([
        adminApi.sources(),
        adminApi.logsScraping(100),
        adminApi.logsNotifications(50),
        adminApi.utilisateurs(),
      ]);
      setSources(src);
      setLogs(scrLogs);
      setNotifLogs(nLogs);
      setUsers(usrs);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const triggerScrape = async (sourceId: string) => {
    setTriggering(sourceId);
    setMessage(null);
    try {
      const result = await adminApi.triggerScraping(sourceId);
      setMessage(
        `Scraping terminé : ${result.nb_offres_nouvelles} nouvelle(s) offre(s). Statut : ${result.statut}`
      );
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur scraping");
    } finally {
      setTriggering(null);
    }
  };

  const deleteUser = async (userId: string, email: string) => {
    if (
      !window.confirm(
        `Supprimer définitivement le compte ${email} et toutes ses données ?`
      )
    ) {
      return;
    }
    setDeletingUserId(userId);
    setMessage(null);
    try {
      await adminApi.deleteUtilisateur(userId);
      setMessage(`Compte ${email} supprimé.`);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur suppression");
    } finally {
      setDeletingUserId(null);
    }
  };

  const createSource = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingSource(true);
    setMessage(null);
    try {
      const created = await adminApi.createSource(newSource);
      setMessage(`Source « ${created.nom} » ajoutée. Vous pouvez lancer le scraping.`);
      setNewSource({ nom: "", pays: "", url_base: "", type_scraping: "html" });
      setShowAddSource(false);
      await load();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Erreur création source");
    } finally {
      setCreatingSource(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "sources", label: "Sources" },
    { id: "scraping", label: "Logs scraping" },
    { id: "notifications", label: "Logs notifications" },
    { id: "users", label: "Utilisateurs" },
  ];

  return (
    <DashboardPage title="Administration" subtitle="Gestion de la plateforme">
      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => setTab(t.id)}
            className={`rounded-xl px-4 py-2 text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand/30 ${
              tab === t.id
                ? "bg-brand text-white shadow-sm shadow-brand/25"
                : "bg-white/80 text-neutral-600 ring-1 ring-neutral-200/60 hover:bg-white"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {message && (
        <div className="mb-4 rounded-2xl border border-brand/20 bg-brand-muted/50 p-4 text-sm text-neutral-700">
          {message}
        </div>
      )}

      {loading ? (
        <LoadingState variant="spinner" />
      ) : (
        <>
          {tab === "sources" && (
            <div className="space-y-4">
              <Card padding="lg">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <h2 className="text-h3 text-neutral-900">Nouvelle source</h2>
                    <p className="text-body-sm text-neutral-600">
                      Toute source ajoutée est scrapée automatiquement via le moteur générique.
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    onClick={() => setShowAddSource((v) => !v)}
                  >
                    {showAddSource ? "Annuler" : "Ajouter une source"}
                  </Button>
                </div>
                {showAddSource && (
                  <form onSubmit={createSource} className="mt-4 grid gap-4 sm:grid-cols-2">
                    <label className="block text-body-sm">
                      <span className="mb-1 block font-medium text-neutral-700">Nom</span>
                      <input
                        required
                        value={newSource.nom}
                        onChange={(e) =>
                          setNewSource((s) => ({ ...s, nom: e.target.value }))
                        }
                        className="w-full rounded-lg border border-neutral-300 px-3 py-2"
                        placeholder="DGMP Côte d'Ivoire"
                      />
                    </label>
                    <label className="block text-body-sm">
                      <span className="mb-1 block font-medium text-neutral-700">Pays</span>
                      <input
                        required
                        value={newSource.pays}
                        onChange={(e) =>
                          setNewSource((s) => ({ ...s, pays: e.target.value }))
                        }
                        className="w-full rounded-lg border border-neutral-300 px-3 py-2"
                        placeholder="Côte d'Ivoire"
                      />
                    </label>
                    <label className="block text-body-sm sm:col-span-2">
                      <span className="mb-1 block font-medium text-neutral-700">URL</span>
                      <input
                        required
                        type="url"
                        value={newSource.url_base}
                        onChange={(e) =>
                          setNewSource((s) => ({ ...s, url_base: e.target.value }))
                        }
                        className="w-full rounded-lg border border-neutral-300 px-3 py-2"
                        placeholder="https://exemple.gov/appels-offres"
                      />
                    </label>
                    <label className="block text-body-sm">
                      <span className="mb-1 block font-medium text-neutral-700">Type</span>
                      <select
                        value={newSource.type_scraping}
                        onChange={(e) =>
                          setNewSource((s) => ({
                            ...s,
                            type_scraping: e.target.value as "html" | "api" | "rss",
                          }))
                        }
                        className="w-full rounded-lg border border-neutral-300 px-3 py-2"
                      >
                        <option value="html">HTML (détection auto)</option>
                        <option value="api">API JSON</option>
                        <option value="rss">Flux RSS / Atom</option>
                      </select>
                    </label>
                    <div className="flex items-end">
                      <Button type="submit" variant="primary" loading={creatingSource}>
                        Enregistrer la source
                      </Button>
                    </div>
                  </form>
                )}
              </Card>

              {sources.map((source) => {
                const lastLog = lastLogBySource[source.id];
                return (
                  <Card key={source.id} padding="lg">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                      <div>
                        <h2 className="text-h3 text-neutral-900">{source.nom}</h2>
                        <p className="text-body-sm text-neutral-600">
                          {source.pays} — {source.url_base} — {source.type_scraping}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          <Badge variant={source.actif ? "actif" : "inactif"}>
                            {source.actif ? "Active" : "Inactive"}
                          </Badge>
                          {lastLog && <StatusBadge statut={lastLog.statut} />}
                        </div>
                        <p className="mt-2 text-body-sm text-neutral-500">
                          Dernière exécution :{" "}
                          {formatDateTime(
                            lastLog?.date_execution ?? source.derniere_execution
                          )}
                        </p>
                        {lastLog?.message_erreur && (
                          <p className="mt-1 text-body-sm text-danger">
                            {lastLog.message_erreur}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="primary"
                        loading={triggering === source.id}
                        onClick={() => triggerScrape(source.id)}
                      >
                        Lancer le scraping
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {tab === "scraping" && (
            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full text-left text-body-sm">
                <thead className="bg-neutral-100 text-neutral-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Source</th>
                    <th className="px-4 py-3 font-medium">Statut</th>
                    <th className="px-4 py-3 font-medium">Trouvées</th>
                    <th className="px-4 py-3 font-medium">Nouvelles</th>
                    <th className="px-4 py-3 font-medium">Erreur</th>
                  </tr>
                </thead>
                <tbody>
                  {logs.map((log) => (
                    <tr key={log.id} className="border-t border-neutral-100">
                      <td className="px-4 py-3">{formatDateTime(log.date_execution)}</td>
                      <td className="px-4 py-3">
                        {sources.find((s) => s.id === log.source_id)?.nom ?? log.source_id}
                      </td>
                      <td className="px-4 py-3">
                        <StatusBadge statut={log.statut} />
                      </td>
                      <td className="px-4 py-3">{log.nb_offres_trouvees}</td>
                      <td className="px-4 py-3">{log.nb_offres_nouvelles}</td>
                      <td className="px-4 py-3 text-danger">
                        {log.message_erreur ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "notifications" && (
            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full text-left text-body-sm">
                <thead className="bg-neutral-100 text-neutral-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Date</th>
                    <th className="px-4 py-3 font-medium">Statut</th>
                    <th className="px-4 py-3 font-medium">Envoyés</th>
                    <th className="px-4 py-3 font-medium">Échecs</th>
                    <th className="px-4 py-3 font-medium">Message</th>
                  </tr>
                </thead>
                <tbody>
                  {notifLogs.map((log) => (
                    <tr key={log.id} className="border-t border-neutral-100">
                      <td className="px-4 py-3">{formatDateTime(log.date_execution)}</td>
                      <td className="px-4 py-3">
                        <StatusBadge statut={log.statut} />
                      </td>
                      <td className="px-4 py-3">{log.nb_emails_envoyes}</td>
                      <td className="px-4 py-3">{log.nb_echecs}</td>
                      <td className="px-4 py-3">{log.message_erreur ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {tab === "users" && (
            <div className="overflow-x-auto rounded-lg border border-neutral-200">
              <table className="min-w-full text-left text-body-sm">
                <thead className="bg-neutral-100 text-neutral-600">
                  <tr>
                    <th className="px-4 py-3 font-medium">Email</th>
                    <th className="px-4 py-3 font-medium">Rôle</th>
                    <th className="px-4 py-3 font-medium">Inscription</th>
                    <th className="px-4 py-3 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id} className="border-t border-neutral-100">
                      <td className="px-4 py-3">{u.email}</td>
                      <td className="px-4 py-3">{u.role}</td>
                      <td className="px-4 py-3">{formatDateTime(u.date_inscription)}</td>
                      <td className="px-4 py-3">
                        {u.id !== currentUser?.id ? (
                          <Button
                            variant="outline"
                            loading={deletingUserId === u.id}
                            onClick={() => deleteUser(u.id, u.email)}
                          >
                            Supprimer
                          </Button>
                        ) : (
                          <span className="text-caption text-neutral-500">Vous</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </DashboardPage>
  );
}
