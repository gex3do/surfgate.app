from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserKeyCreateIn(BaseModel):
    firstname: str = Field(min_length=3, max_length=80)
    lastname: str = Field(min_length=3, max_length=80)
    email: EmailStr

    months: int | None = Field(default=12, le=60)
    demo: bool | None = False
    order_id: str | None = Field(default="", min_length=0, max_length=15)


class UserCreateIn(BaseModel):
    firstname: str = Field(min_length=3, max_length=80)
    lastname: str = Field(min_length=3, max_length=80)
    email: EmailStr


class KeyCreateIn(BaseModel):
    user_uuid: UUID
    months: int | None = Field(default=1, le=60)
    demo: bool | None = False
    order_id: str | None = Field("", min_length=0, max_length=15)


class KeyDeleteByOrderIdIn(BaseModel):
    user_uuid: UUID
    order_id: str | None = Field(min_length=1, max_length=15)


class KeyGetIn(BaseModel):
    key: UUID


class KeyUpdateFrequencyIn(BaseModel):
    key: UUID
    frequency: int = Field(min_length=0, max_length=99999)


class KeyUpdatePeriodIn(BaseModel):
    key: UUID
    months: int = Field(le=60)


class UserKeyDeleteOut(BaseModel):
    status: str = "deleted"


class UserCreateOut(BaseModel):
    uuid: UUID
    status: str = "created"


class UserKeyCreateOut(BaseModel):
    user_uuid: UUID
    key: str
    valid_from: str
    valid_to: str
    requests_left: int | None = None


class KeyCreateOut(BaseModel):
    key: UUID


class KeyGetOut(BaseModel):
    key: UUID
