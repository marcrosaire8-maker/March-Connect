from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.base import MongoModel, PyObjectId


class SecteurBase(BaseModel):
    nom: str
    mots_cles: list[str]


class SecteurCreate(SecteurBase):
    pass


class SecteurInDB(SecteurBase, MongoModel):
    pass


class SecteurDocument(SecteurBase):
    model_config = ConfigDict(populate_by_name=True)

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
