from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.enums import MemberRole


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrganizationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    created_at: datetime


class MemberAdd(BaseModel):
    email: EmailStr
    role: MemberRole


class MemberRead(BaseModel):
    id: int
    user_id: int
    email: EmailStr
    full_name: str
    role: MemberRole
    created_at: datetime
