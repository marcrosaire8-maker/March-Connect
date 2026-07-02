from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.enums import ScrapingType
from app.schemas.base import MongoModel, PyObjectId


class SourceBase(BaseModel):
    nom: str
    pays: str
    url_base: str
    type_scraping: ScrapingType
    actif: bool = True
    config: dict[str, Any] = Field(default_factory=dict)
    derniere_execution: Optional[datetime] = None


class SourceCreate(SourceBase):
    pass


class SourceInDB(SourceBase, MongoModel):
    pass


class SourceDocument(SourceBase):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
