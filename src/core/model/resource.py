from enum import StrEnum
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from src.core.AppEnum import ResourceType


class Lang(StrEnum):
    english = "english"
    german = "german"
    russian = "russian"


def validate_type(res_type: str, info: ValidationInfo):
    if res_type != ResourceType.URL:
        return res_type

    value = info.data.get("value", None)
    if value is None:
        # pass further and let fastapi recognize and inform about a missing field
        return res_type

    # noinspection PyUnresolvedReferences
    value = value.lower()

    # noinspection HttpUrlsUsage
    if value.startswith("http://") or value.startswith("https://"):
        return res_type

    raise ValueError("Please provide a valid URL")


class ResourcePredictGetIn(BaseModel):
    value: str = Field(min_length=2, max_length=2000)
    type: Literal[ResourceType.URL, ResourceType.TEXT, ResourceType.FILE]
    top_features: bool | None = False

    # noinspection PyNestedDecorators
    @field_validator("type", mode="after")
    @classmethod
    def validate_type(cls, res_type: str, info: ValidationInfo):
        return validate_type(res_type, info)


class ResourcePredictRateIn(BaseModel):
    value: str = Field(min_length=2, max_length=2000)
    type: Literal[ResourceType.URL, ResourceType.TEXT, ResourceType.FILE]
    top_features: bool | None = False
    recheck: bool | None = False
    lang: Literal[Lang.english, Lang.german, Lang.russian] | None = None

    # noinspection PyNestedDecorators
    @field_validator("type", mode="after")
    @classmethod
    def validate_type(cls, res_type: str, info: ValidationInfo):
        return validate_type(res_type, info)


class ResourcePredictGetOrRateOut(BaseModel):
    result: str = Field(max_length=30)
    top_features: Optional[dict] = None
