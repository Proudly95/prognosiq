from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routes.orgs import AdminMember, get_current_org_member, require_role
from app.core.db import get_db
from app.core.pagination import PageParams
from app.models.asset import Asset
from app.models.enums import MemberRole, WorkOrderStatus
from app.models.member import OrganizationMember
from app.models.work_order import WorkOrder
from app.schemas.work_order import (
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderPage,
    WorkOrderUpdate,
)

router = APIRouter(prefix="/{org_id}/work-orders", tags=["work orders"])

# Role walls, same policy as the assets routes (see there for the rationale):
#   viewer  -> read-only
#   agent   -> can create/update
#   admin   -> can delete
AgentOrAdmin = Annotated[
    OrganizationMember, Depends(require_role(MemberRole.AGENT, MemberRole.ADMIN))
]


# ------ LIST (paginated, filterable) -- viewer and up ---------------------------


@router.get("", response_model=WorkOrderPage)
def list_work_orders(
    member: OrganizationMember = Depends(get_current_org_member),
    params: PageParams = Depends(),
    asset_id: int | None = Query(None),
    status: WorkOrderStatus | None = Query(None),
    db: Session = Depends(get_db),
):
    filters = [WorkOrder.organization_id == member.organization_id]
    if asset_id is not None:
        filters.append(WorkOrder.asset_id == asset_id)
    if status is not None:
        filters.append(WorkOrder.status == status)

    total = db.scalar(select(func.count()).select_from(WorkOrder).where(*filters))
    rows = db.scalars(
        select(WorkOrder)
        .where(*filters)
        .order_by(WorkOrder.id)
        .offset(params.offset)
        .limit(params.limit)
    ).all()
    return {"items": rows, "total": total, "page": params.page, "size": params.size}


# -- Create -- agent and up -------------------------------------------------------


@router.post("", response_model=WorkOrderOut, status_code=201)
def create_work_order(
    payload: WorkOrderCreate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    # The target asset must exist inside THIS org — never create a work order
    # against another org's asset (org scoping, same rule as get_one below).
    asset = db.scalar(
        select(Asset).where(
            Asset.id == payload.asset_id,
            Asset.organization_id == member.organization_id,
        )
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    work_order = WorkOrder(
        organization_id=member.organization_id,
        created_by_id=member.user_id,
        **payload.model_dump(),
    )
    db.add(work_order)
    db.commit()
    db.refresh(work_order)
    return work_order


# -- GET ONE -- viewer and up ------------------------------------------------------


@router.get("/{work_order_id}", response_model=WorkOrderOut)
def get_work_order(
    work_order_id: int,
    member: OrganizationMember = Depends(get_current_org_member),
    db: Session = Depends(get_db),
):
    # Both filters — never by id alone, or org A could read org B's work orders
    work_order = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == member.organization_id,
        )
    )
    if work_order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    return work_order


# == UPDATE (partial) -- agent and up ----------------------------------------------


@router.patch("/{work_order_id}", response_model=WorkOrderOut)
def update_work_order(
    work_order_id: int,
    payload: WorkOrderUpdate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    work_order = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == member.organization_id,
        )
    )
    if work_order is None:
        raise HTTPException(status_code=404, detail="Work order not found")

    # exclude_unset = only touch fields the client actually sent
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(work_order, field, value)
    db.commit()
    db.refresh(work_order)
    return work_order


# -- DELETE -- admin only -----------------------------------------------------------


@router.delete("/{work_order_id}", status_code=204)
def delete_work_order(
    work_order_id: int,
    member: AdminMember,
    db: Session = Depends(get_db),
):
    work_order = db.scalar(
        select(WorkOrder).where(
            WorkOrder.id == work_order_id,
            WorkOrder.organization_id == member.organization_id,
        )
    )
    if work_order is None:
        raise HTTPException(status_code=404, detail="Work order not found")
    db.delete(work_order)
    db.commit()
