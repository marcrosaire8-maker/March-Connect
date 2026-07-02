from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import MongoModel, PyObjectId


class OffreBase(BaseModel):
    source_id: PyObjectId
    secteur_id: Optional[PyObjectId] = None
    titre: str
    organisme: str
    pays: str
    description: str
    date_publication: Optional[datetime] = None
    date_limite: Optional[datetime] = None
    montant_estime: Optional[str] = None
    lien_source: str
    contact: Optional[dict[str, str]] = None
    hash_unique: str
    date_scraping: datetime


class OffreCreate(OffreBase):
    pass


class OffreInDB(OffreBase, MongoModel):
    pass


class OffreDocument(OffreBase):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
