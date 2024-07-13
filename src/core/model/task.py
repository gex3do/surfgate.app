from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from src.core.model.resource import Lang


class TaskCreateIn(BaseModel):
    value: str = Field(min_length=2, max_length=2000)
    return_url: str = Field(min_length=4, max_length=2000)

    max_depth: int | None = Field(default=1, ge=0, le=2)
    lang: Literal[Lang.english, Lang.german, Lang.russian] | None = None
    recheck: bool | None = False


class TaskGetIn(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    top_features: bool | None = False


class TaskCreateOut(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)


class TaskCreateNotification(BaseModel):
    uuid: UUID = Field(default_factory=uuid4)
    status: str

    def to_dict(self):
        return {"uuid": str(self.uuid), "status": self.status}


class TaskGetOut(BaseModel):
    page: Any
    stats: Any
