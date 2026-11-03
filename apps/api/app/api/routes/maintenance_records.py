from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routes.orgs import AdminMember, get_current_org_member, require_role
from app.core.db import get_db
from app.core.pagination import PageParams
from app.models.asset import Asset
from app.models.enums import MemberRole
from app.models.maintenance_record import MaintenanceRecord
from app.models.member import OrganizationMember
from app.schemas.maintenance_record import (
    MaintenanceRecordCreate,
    MaintenanceRecordOut,
    MaintenanceRecordPage,
    MaintenanceRecordUpdate,
)

router = APIRouter(
    prefix="/{org_id}/assets/{asset_id}/maintenance-records",
    tags=["maintenance records"],
)

# Role walls, reused from the orgs routes (one source of truth):
#   viewer  -> read-only
#   agent   -> can create/update
#   admin   -> can delete
AgentOrAdmin = Annotated[
    OrganizationMember, Depends(require_role(MemberRole.AGENT, MemberRole.ADMIN))
]


def _get_org_asset(db: Session, asset_id: int, organization_id: int) -> Asset:
    # Both filters — never by id alone, or org A could reach org B's assets
    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == organization_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# -------- LIST (paginated) -- viewer and up --------------------------------------


@router.get("", response_model=MaintenanceRecordPage)
def list_maintenance_records(
    asset_id: int,
    member: OrganizationMember = Depends(get_current_org_member),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    _get_org_asset(db, asset_id, member.organization_id)
    total = db.scalar(
        select(func.count())
        .select_from(MaintenanceRecord)
        .where(MaintenanceRecord.asset_id == asset_id)
    )
    rows = db.scalars(
        select(MaintenanceRecord)
        .where(MaintenanceRecord.asset_id == asset_id)
        .order_by(MaintenanceRecord.id)
        .offset(params.offset)
        .limit(params.limit)
    ).all()
    return {"items": rows, "total": total, "page": params.page, "size": params.size}


# -- Create - agent and up ---------------------------------------------------------


@router.post("", response_model=MaintenanceRecordOut, status_code=201)
def create_maintenance_record(
    asset_id: int,
    payload: MaintenanceRecordCreate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    _get_org_asset(db, asset_id, member.organization_id)
    record = MaintenanceRecord(asset_id=asset_id, **payload.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


# -- GET ONE - viewer and up -------------------------------------------------------


@router.get("/{record_id}", response_model=MaintenanceRecordOut)
def get_maintenance_record(
    asset_id: int,
    record_id: int,
    member: OrganizationMember = Depends(get_current_org_member),
    db: Session = Depends(get_db),
):
    _get_org_asset(db, asset_id, member.organization_id)
    record = db.scalar(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id,
            MaintenanceRecord.asset_id == asset_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return record


# == UPDATE (partial) - agent and up -----------------------------------------------


@router.patch("/{record_id}", response_model=MaintenanceRecordOut)
def update_maintenance_record(
    asset_id: int,
    record_id: int,
    payload: MaintenanceRecordUpdate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    _get_org_asset(db, asset_id, member.organization_id)
    record = db.scalar(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id,
            MaintenanceRecord.asset_id == asset_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    # exclude_unset = only touch fields the client actually sent
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    db.commit()
    db.refresh(record)
    return record


# -- DELETE -- admin only -----------------------------------------------------------


@router.delete("/{record_id}", status_code=204)
def delete_maintenance_record(
    asset_id: int,
    record_id: int,
    member: AdminMember,
    db: Session = Depends(get_db),
):
    _get_org_asset(db, asset_id, member.organization_id)
    record = db.scalar(
        select(MaintenanceRecord).where(
            MaintenanceRecord.id == record_id,
            MaintenanceRecord.asset_id == asset_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    db.delete(record)
    db.commit()
