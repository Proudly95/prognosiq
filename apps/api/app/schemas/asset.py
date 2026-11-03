from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AssetType


class AssetCreate(BaseModel):
    name: str
    asset_type: AssetType
    serial_number: str | None = None
    installed_at: datetime | None = None
    is_active: bool = True


class AssetUpdate(BaseModel):
    name: str | None = None
    asset_type: AssetType | None = None
    serial_number: str | None = None
    installed_at: datetime | None = None
    is_active: bool | None = None


class AssetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    name: str
    asset_type: AssetType
    serial_number: str | None
    installed_at: datetime | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssetPage(BaseModel):
    items: list[AssetOut]
    total: int
    page: int
    size: int
