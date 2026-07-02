from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ScrapingStatus
from app.schemas.base import MongoModel, PyObjectId


class LogScrapingBase(BaseModel):
    source_id: PyObjectId
    date_execution: datetime
    statut: ScrapingStatus
    nb_offres_trouvees: int
    nb_offres_nouvelles: int
    message_erreur: Optional[str] = None


class LogScrapingCreate(LogScrapingBase):
    pass


class LogScrapingInDB(LogScrapingBase, MongoModel):
    pass


class LogScrapingDocument(LogScrapingBase):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
