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
