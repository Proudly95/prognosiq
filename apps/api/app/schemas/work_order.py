from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import WorkOrderPriority, WorkOrderSource, WorkOrderStatus


class WorkOrderCreate(BaseModel):
    asset_id: int
    title: str
    description: str
    assignee_id: int | None = None
    priority: WorkOrderPriority = WorkOrderPriority.NORMAL
    category: str | None = None
    source: WorkOrderSource = WorkOrderSource.MANUAL
    due_at: datetime | None = None
    # NOTE: no `status` on create — work orders always start OPEN (model
    # default); transitions happen through PATCH.


class WorkOrderUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None
    status: WorkOrderStatus | None = None
    priority: WorkOrderPriority | None = None
    category: str | None = None
    due_at: datetime | None = None


class WorkOrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    asset_id: int
    assignee_id: int | None
    created_by_id: int | None
    title: str
    description: str
    status: WorkOrderStatus
    priority: WorkOrderPriority
    category: str | None
    source: WorkOrderSource
    due_at: datetime | None
    created_at: datetime
    updated_at: datetime


class WorkOrderPage(BaseModel):
    items: list[WorkOrderOut]
    total: int
    page: int
    size: int
