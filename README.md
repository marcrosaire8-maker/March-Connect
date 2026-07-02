# MarchéConnect

Plateforme de veille sur les appels d'offres en Afrique de l'Ouest.

## Structure

| Dossier | Rôle |
|---------|------|
| `backend/` | API FastAPI, MongoDB, scrapers, notifications, scheduler |
| `frontend/` | React 19, Vite, TypeScript, Tailwind |
| `docs/` | Guides Word (rapport final, configuration livraison) |
| `render.yaml` | Blueprint déploiement Render (API + site statique) |

## Démarrage rapide (local)

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # renseigner les variables
uvicorn main:app --reload --port 8000

# Frontend (autre terminal)
cd frontend
npm install
cp .env.example .env   # optionnel en dev
npm run dev
```

- Application : http://localhost:5173
- API : http://localhost:8000
- Santé : http://localhost:8000/health

## Variables d'environnement

### Backend (`backend/.env`)

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `MONGODB_URI` | Oui | Chaîne MongoDB Atlas |
| `MONGODB_DB_NAME` | Non | Nom de la base (défaut : `marches_publics_ouest`) |
| `JWT_SECRET` | Oui | Secret long et aléatoire pour les jetons |
| `ADMIN_EMAIL` | Oui | Email du compte administrateur initial |
| `ADMIN_PASSWORD` | Oui | Mot de passe admin (8+ caractères, complexité) |
| `FRONTEND_URL` | Oui | URL du frontend (CORS, liens email) |
| `SMTP_HOST` | Oui* | Serveur SMTP (ex. `smtp-relay.brevo.com`) |
| `SMTP_PORT` | Non | Port SMTP (défaut : 587) |
| `SMTP_USER` | Oui* | Identifiant SMTP |
| `SMTP_PASSWORD` | Oui* | Mot de passe / clé SMTP |
| `SMTP_FROM` | Oui* | Expéditeur `Nom <email@domaine.com>` |
| `GOOGLE_CLIENT_ID` | Recommandé | Client OAuth Google (Application Web) |
| `APPLE_CLIENT_ID` | Optionnel | Services ID Apple Sign-In |
| `NOTIFICATION_INTERVAL_MINUTES` | Non | Alertes email (défaut : 15) |
| `NOTIFICATION_HOUR` / `NOTIFICATION_MINUTE` | Non | Ancrage horaire des alertes |
| `SCRAPE_INTERVAL_MINUTES` | Non | Collecte offres (défaut : 30) |

\* Requis pour les emails transactionnels (bienvenue, OTP, alertes).

### Frontend (`frontend/.env`)

| Variable | Obligatoire | Description |
|----------|-------------|-------------|
| `VITE_GOOGLE_CLIENT_ID` | Recommandé | Même valeur que `GOOGLE_CLIENT_ID` |
| `VITE_APPLE_CLIENT_ID` | Optionnel | Même valeur que `APPLE_CLIENT_ID` |
| `VITE_API_URL` | Prod seulement | URL API complète avec `/api` |

> Les variables `VITE_*` sont compilées au build. Toute modification exige un rebuild du frontend.

Modèle complet : `backend/.env.example`, `frontend/.env.example`.

## Tests et CI

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

GitHub Actions (`.github/workflows/ci.yml`) exécute les tests backend et le build frontend sur chaque push/PR vers `main`.

## Déploiement sur Render

### Services

| Service | Type | Rôle |
|---------|------|------|
| `marcheconnect-api` | Web (Python) | API FastAPI + scheduler |
| `marcheconnect-web` | Static Site | Frontend React |

### Procédure

1. Pousser le dépôt sur GitHub.
2. Render → **New → Blueprint** → connecter le repo.
3. Renseigner les variables `sync: false` (secrets) dans le dashboard.
4. **Apply** et attendre le déploiement (~5–10 min).
5. Vérifier :
   - https://marcheconnect-api.onrender.com/health
   - https://marcheconnect-web.onrender.com/connexion

### Variables Render — API (`marcheconnect-api`)

`MONGODB_URI`, `JWT_SECRET`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`

`FRONTEND_URL` est liée automatiquement à l'URL du site statique.

### Variables Render — Frontend (`marcheconnect-web`)

`VITE_GOOGLE_CLIENT_ID` (identique au backend). `MARCHECONNECT_API_URL` est liée à l'API.

Après toute modification de `VITE_*` : **Manual Deploy** du service web.

### Google Sign-In en production

Voir `docs/GOOGLE_PRODUCTION.md`. Checklist minimale :

1. Origines JavaScript autorisées : `https://marcheconnect-web.onrender.com`
2. URI de redirection : même URL
3. `GOOGLE_CLIENT_ID` (API) = `VITE_GOOGLE_CLIENT_ID` (web)
4. Écran de consentement OAuth en mode **Production** ou testeurs ajoutés

### Emails en production (Brevo SMTP)

Voir `docs/BREVO_SETUP.md`. Résumé :

1. Compte Brevo + expéditeur vérifié (sans domaine custom possible pour les tests)
2. Clé SMTP → variables `SMTP_*` sur Render
3. Supprimer d'éventuelles variables `RESEND_*` restantes sur Render

## Rollback en cas de problème

### Frontend ou API (Render)

1. Render → service concerné → **Deploys**.
2. Sélectionner un déploiement précédent → **Rollback to this deploy**.

### Base de données

1. MongoDB Atlas → **Backup** (si activé) → restaurer un snapshot.
2. Pour une purge accidentelle : utiliser les exports JSON de `backend/backups/` (script `purge_non_admin_users.py`).

### Secrets compromis

1. Régénérer `JWT_SECRET` sur Render → redéployer l'API (sessions invalidées).
2. Changer `ADMIN_PASSWORD` + exécuter `python scripts/create_admin.py --reset-password`.
3. Rotation mot de passe MongoDB Atlas + mise à jour `MONGODB_URI`.

## Scripts utiles

```bash
# Créer / promouvoir un admin
python scripts/create_admin.py --email admin@example.com --password "Motdepasse1!"

# Purge des comptes (avec sécurité)
python scripts/purge_non_admin_users.py --dry-run
python scripts/purge_non_admin_users.py   # demande confirmation SUPPRIMER + backup JSON
```

## Plan gratuit Render

- L'API s'endort après ~15 min d'inactivité (première requête lente).
- Le scheduler tourne sur l'instance API ; pour une veille 24/7 fiable, passer au plan payant.

## Documentation complémentaire

- `docs/Rapport_Final_MarcheConnect.docx` — historique de développement
- `docs/Guide_Configuration_MarcheConnect.docx` — mise en service après livraison
- `docs/GOOGLE_PRODUCTION.md` — checklist Google Sign-In
- `docs/BREVO_SETUP.md` — configuration Brevo (avec ou sans domaine)
