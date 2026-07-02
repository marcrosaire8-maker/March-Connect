# Checklist Google Sign-In — production Render
#
# À faire AVANT de tester « Continuer avec Google » en ligne.
# Client ID actuel (dev) : voir backend/.env — réutiliser le MÊME en prod.

## 1. Google Cloud Console

URL : https://console.cloud.google.com/apis/credentials

Client OAuth → type **Application Web** → modifier :

### Origines JavaScript autorisées
- http://localhost:5173          (dev)
- http://127.0.0.1:5173          (dev)
- https://VOTRE-URL.onrender.com (prod — URL exacte du frontend Render)

### URI de redirection autorisés
- https://VOTRE-URL.onrender.com

Enregistrer. Les changements peuvent prendre quelques minutes.

## 2. Écran de consentement OAuth

URL : https://console.cloud.google.com/apis/credentials/consent

- Mode **Test** : seuls les utilisateurs ajoutés comme « testeurs » peuvent se connecter.
- Mode **Production** : ouvert à tous (validation Google si scopes sensibles).

## 3. Variables Render

| Service            | Variable              | Valeur                          |
|--------------------|-----------------------|---------------------------------|
| marcheconnect-api  | GOOGLE_CLIENT_ID      | xxx.apps.googleusercontent.com  |
| marcheconnect-web  | VITE_GOOGLE_CLIENT_ID | **identique** au backend        |

Le backend vérifie le jeton ; le frontend l'utilise pour afficher le bouton Google.

## 4. Vérification

1. https://VOTRE-API.onrender.com/api/auth/google/config  
   → `{"enabled": true, "client_id": "..."}`
2. Page `/connexion` → bouton Google cliquable (pas grisé)
3. Connexion Google → redirection tableau de bord

## Erreurs fréquentes

| Erreur              | Cause                                      |
|---------------------|--------------------------------------------|
| origin_mismatch     | URL prod absente des origines JS Google    |
| Bouton désactivé    | GOOGLE_CLIENT_ID manquant sur Render       |
| 401 / jeton invalide| Client ID différent entre front et backend |
| Accès refusé        | App OAuth en mode Test, email non testeur  |
