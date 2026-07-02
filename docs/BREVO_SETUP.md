# Configuration Brevo (sans domaine personnalisé)

En attendant l'achat d'un domaine, vous pouvez envoyer des emails via Brevo en **vérifiant une adresse expéditeur** (pas besoin de DKIM sur domaine custom).

## Étapes

### 1. Créer un compte Brevo

https://www.brevo.com — plan gratuit : 300 emails/jour.

### 2. Vérifier un expéditeur (email unique)

1. Brevo → **Settings** → **Senders, domains & dedicated IPs** → **Senders**
2. **Add a sender** → saisir votre email (ex. `marcrosaire8@gmail.com` ou une adresse pro)
3. Confirmer le lien reçu par email

> Sans domaine vérifié, l'expéditeur doit être une adresse que vous contrôlez. Les emails partent via l'infrastructure Brevo (délivrabilité correcte pour les tests, moins idéale qu'avec DKIM domaine).

### 3. Créer une clé SMTP

1. Brevo → **SMTP & API** → **SMTP**
2. Générer une **clé SMTP** (mot de passe dédié)

### 4. Variables Render (`marcheconnect-api`)

| Variable | Valeur |
|----------|--------|
| `SMTP_HOST` | `smtp-relay.brevo.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Votre login SMTP Brevo (souvent votre email de compte) |
| `SMTP_PASSWORD` | Clé SMTP générée |
| `SMTP_FROM` | `MarchéConnect <email-expediteur-verifie@...>` |

**Supprimez** `RESEND_API_KEY` et `RESEND_FROM_EMAIL` du dashboard Render si encore présents.

Redéployez l'API après modification.

### 5. Vérification

1. Logs API au démarrage : `Emails transactionnels : SMTP actif`
2. Inscription test → compte créé même si email échoue
3. Email de bienvenue reçu (vérifier spams)

## Migration vers votre domaine (plus tard)

1. Acheter le domaine (~10–15 $/an)
2. Brevo → **Domains** → ajouter le domaine
3. Configurer les enregistrements DNS **SPF**, **DKIM** (et **DMARC** recommandé)
4. Mettre à jour `SMTP_FROM` : `MarchéConnect <alertes@votredomaine.com>`
5. Re-vérifier l'expéditeur domaine dans Brevo

Aucun changement de code requis — uniquement DNS + variables d'environnement.
