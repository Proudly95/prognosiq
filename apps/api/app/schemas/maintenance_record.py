from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MaintenanceRecordCreate(BaseModel):
    performed_at: datetime
    notes: str | None = None


class MaintenanceRecordUpdate(BaseModel):
    performed_at: datetime | None = None
    notes: str | None = None


class MaintenanceRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    performed_at: datetime
    notes: str | None
    created_at: datetime
    updated_at: datetime


class MaintenanceRecordPage(BaseModel):
    items: list[MaintenanceRecordOut]
    total: int
    page: int
    size: int
