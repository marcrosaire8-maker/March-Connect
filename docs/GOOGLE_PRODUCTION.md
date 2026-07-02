# Checklist Google Sign-In — production Render

À faire AVANT de tester « Continuer avec Google » en ligne.

## Diagnostic production (02/07/2026)

| Vérification | Résultat |
|--------------|----------|
| Headers COOP sur `marcheconnect-web.onrender.com` | `same-origin-allow-popups` ✅ |
| Headers COEP | `unsafe-none` ✅ |
| `GET /api/auth/google/config` | `enabled: true` + `client_id` présent ✅ |
| `GET /health` | `ok` ✅ |

Les en-têtes COOP/COEP sont corrects dans `render.yaml` et **déployés en production**.
Si des erreurs COOP apparaissent encore dans la console, vérifier plutôt :
- cache navigateur (test navigation privée)
- double initialisation GSI (avertissement `initialize() called multiple times`)
- `origin_mismatch` côté Google Console (origine prod absente)

## 1. Google Cloud Console

URL : https://console.cloud.google.com/apis/credentials

Client OAuth → type **Application Web** → modifier :

### Origines JavaScript autorisées
- `http://localhost:5173` (dev)
- `http://127.0.0.1:5173` (dev)
- `https://marcheconnect-web.onrender.com` (prod — URL exacte, sans slash final)

### URI de redirection autorisés
- `https://marcheconnect-web.onrender.com`

Enregistrer. Les changements peuvent prendre quelques minutes.

## 2. Écran de consentement OAuth

URL : https://console.cloud.google.com/apis/credentials/consent

- Mode **Test** : seuls les utilisateurs ajoutés comme « testeurs » peuvent se connecter.
- Mode **Production** : ouvert à tous (validation Google si scopes sensibles).

## 3. Variables Render

| Service | Variable | Valeur |
|---------|----------|--------|
| marcheconnect-api | `GOOGLE_CLIENT_ID` | `xxx.apps.googleusercontent.com` |
| marcheconnect-api | `FRONTEND_URL` | `https://marcheconnect-web.onrender.com` |
| marcheconnect-web | `VITE_GOOGLE_CLIENT_ID` | **identique** au backend |

Le backend vérifie le jeton ; le frontend l'utilise pour afficher le bouton Google.

**Après modification de `VITE_GOOGLE_CLIENT_ID` : Manual Deploy du service web** (rebuild obligatoire).

## 4. Vérification

1. DevTools → Network → document `/` → Response Headers :
   - `cross-origin-opener-policy: same-origin-allow-popups`
2. https://marcheconnect-api.onrender.com/api/auth/google/config  
   → `{"enabled": true, "client_id": "..."}`
3. Page `/connexion` → bouton Google cliquable (pas grisé)
4. Connexion Google → redirection tableau de bord

## Erreurs fréquentes

| Erreur | Cause | Action |
|--------|-------|--------|
| `origin_mismatch` | URL prod absente des origines JS Google | Ajouter l'URL exacte dans Google Console |
| Bouton désactivé | `GOOGLE_CLIENT_ID` manquant ou build frontend obsolète | Vérifier env Render + redeploy web |
| 401 / jeton invalide | Client ID différent entre front et backend | Aligner les deux variables |
| Accès refusé | App OAuth en mode Test, email non testeur | Passer en Production ou ajouter testeurs |
| COOP warnings | Souvent bénins avec `same-origin-allow-popups` | Vérifier headers ; ignorer si connexion réussit |
| 503 sur `/auth/google` | API en cold start (plan gratuit Render) | Réessayer après ~30 s |
