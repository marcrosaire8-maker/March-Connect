from datetime import datetime
from typing import Annotated, Any

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_object_id(value: Any) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    if isinstance(value, str) and ObjectId.is_valid(value):
        return ObjectId(value)
    raise ValueError("Identifiant MongoDB invalide")


PyObjectId = Annotated[ObjectId, Field(...)]


class MongoModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
    )

    id: PyObjectId = Field(alias="_id")

    @field_validator("id", mode="before")
    @classmethod
    def parse_id(cls, value: Any) -> ObjectId:
        if value is None:
            raise ValueError("L'identifiant est requis")
        return validate_object_id(value)
