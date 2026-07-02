# MarchéConnect

Plateforme de veille sur les appels d'offres en Afrique de l'Ouest.

## Structure

- `backend/` — API FastAPI, MongoDB, scrapers, notifications
- `frontend/` — React 19, Vite, TypeScript, Tailwind

## Démarrage rapide

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # puis renseigner les variables
uvicorn main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.example .env   # optionnel
npm run dev
```

- Application : http://localhost:5173
- API : http://localhost:8000

## Configuration

Copiez les fichiers `.env.example` vers `.env` dans `backend/` et `frontend/`, puis renseignez au minimum :

- `MONGODB_URI`, `JWT_SECRET`
- `GOOGLE_CLIENT_ID` / `APPLE_CLIENT_ID` pour l'authentification sociale

## Déploiement sur Render

Le fichier `render.yaml` à la racine décrit deux services :

| Service | Type | Rôle |
|---------|------|------|
| `marcheconnect-api` | Web (Python) | API FastAPI |
| `marcheconnect-web` | Static Site | Frontend React |

### Étapes

1. Poussez ce dépôt sur GitHub (`March-Connect`).
2. Créez un compte sur [render.com](https://render.com).
3. **New → Blueprint** → connectez le repo `marcrosaire8-maker/March-Connect`.
4. Render détecte `render.yaml` et propose les 2 services.
5. Renseignez les variables marquées **sync: false** :
   - `MONGODB_URI` (MongoDB Atlas — autorisez `0.0.0.0/0` ou les IP Render)
   - `ADMIN_EMAIL` / `ADMIN_PASSWORD`
   - `GOOGLE_CLIENT_ID`, `APPLE_CLIENT_ID` (optionnel)
   - SMTP ou `RESEND_API_KEY` pour les emails
6. Cliquez **Apply** et attendez le déploiement (~5–10 min).

### URLs après déploiement

- Frontend : `https://marcheconnect-web.onrender.com`
- API : `https://marcheconnect-api.onrender.com`
- Santé : `https://marcheconnect-api.onrender.com/health`

### OAuth en production

#### Google Sign-In (obligatoire avant mise en ligne)

1. Ouvrez [Google Cloud Console → Credentials](https://console.cloud.google.com/apis/credentials).
2. Sélectionnez votre **OAuth 2.0 Client ID** de type **Application Web** (le même que `GOOGLE_CLIENT_ID`).
3. Dans **Origines JavaScript autorisées**, ajoutez **en plus** de localhost :
   ```
   https://marcheconnect-web.onrender.com
   ```
   (Remplacez par votre URL Render réelle ou domaine personnalisé.)
4. Dans **URI de redirection autorisés**, ajoutez la même URL :
   ```
   https://marcheconnect-web.onrender.com
   ```
5. Sur **Render**, renseignez le **même** Client ID à deux endroits :
   - Service `marcheconnect-api` → `GOOGLE_CLIENT_ID`
   - Service `marcheconnect-web` → `VITE_GOOGLE_CLIENT_ID`
6. Si l'écran de consentement OAuth est en mode **Test**, ajoutez les emails des testeurs dans [OAuth consent screen](https://console.cloud.google.com/apis/credentials/consent).

Sans l'étape 3, Google renverra `origin_mismatch` et le bouton « Continuer avec Google » ne fonctionnera pas en production.

#### Apple Sign-In

### Plan gratuit Render

- L'API s'endort après ~15 min d'inactivité (première requête lente).
- Le scheduler tourne sur l'instance API ; pour une veille 24/7 fiable, passez au plan payant.
