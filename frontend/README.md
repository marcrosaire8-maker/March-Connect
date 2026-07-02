# Frontend — Marchés Publics Ouest

Stack : Vite + React + TypeScript + Tailwind CSS.

## Développement

```bash
# Terminal 1 — backend
cd backend && .venv/bin/uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm install && npm run dev
```

- App : http://localhost:5173
- API (proxy dev) : http://localhost:5173/api → backend :8000
- Style guide (dev only) : http://localhost:5173/style-guide

## Pages

| Route | Accès |
|-------|--------|
| `/` | Public — offres + sidebar secteurs |
| `/connexion`, `/inscription` | Public |
| `/offres`, `/mon-compte`, `/calendrier` | Connecté |
| `/admin` | Admin uniquement |

## Charte graphique

- Tokens : `tailwind.config.js`
- Composants : `src/components/`
- JWT stocké en `sessionStorage` (session navigateur)
