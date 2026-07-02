from fastapi import APIRouter

from app.api import abonnes, admin, auth, favoris, logs, notifications, offres, scraping, secteurs, sources, suivis_sites

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router)
api_router.include_router(admin.router)
api_router.include_router(offres.router)
api_router.include_router(favoris.router)
api_router.include_router(secteurs.router)
api_router.include_router(sources.router)
api_router.include_router(scraping.router)
api_router.include_router(logs.router)
api_router.include_router(abonnes.router)
api_router.include_router(suivis_sites.router)
api_router.include_router(notifications.router)
