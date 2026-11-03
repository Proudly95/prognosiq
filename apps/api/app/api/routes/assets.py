from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.routes.orgs import AdminMember, get_current_org_member, require_role
from app.core.db import get_db
from app.core.pagination import PageParams
from app.models.asset import Asset
from app.models.enums import MemberRole
from app.models.member import OrganizationMember
from app.schemas.asset import AssetCreate, AssetOut, AssetPage, AssetUpdate

router = APIRouter(prefix="/{org_id}/assets", tags=["assets"])

# Role walls, reused from the orgs routes (one source of truth):
#   viewer  -> read-only
#   agent   -> can create/update
#   admin   -> can delete
AgentOrAdmin = Annotated[
    OrganizationMember, Depends(require_role(MemberRole.AGENT, MemberRole.ADMIN))
]


# --------LIST (paginated) -- viewer and up --------------------------------------


@router.get("", response_model=AssetPage)
def list_assets(
    member: OrganizationMember = Depends(get_current_org_member),
    params: PageParams = Depends(),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count())
        .select_from(Asset)
        .where(Asset.organization_id == member.organization_id)
    )
    rows = db.scalars(
        select(Asset)
        .where(Asset.organization_id == member.organization_id)
        .order_by(Asset.id)
        .offset(params.offset)
        .limit(params.limit)
    ).all()
    return {"items": rows, "total": total, "page": params.page, "size": params.size}


# -- Create - agent and up -------------------------------------------------------


@router.post("", response_model=AssetOut, status_code=201)
def create_asset(
    payload: AssetCreate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    asset = Asset(organization_id=member.organization_id, **payload.model_dump())
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


# -- GET ONE - viewer and up -------------------------------------------------------


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(
    asset_id: int,
    member: OrganizationMember = Depends(get_current_org_member),
    db: Session = Depends(get_db),
):
    # Both filters — never by id alone, or org A could read org B's assets
    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == member.organization_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


# == UPDATE (partial) - agent and up -----------------------------------------------


@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: int,
    payload: AssetUpdate,
    member: AgentOrAdmin,
    db: Session = Depends(get_db),
):
    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == member.organization_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")

    # exclude_unset = only touch fields the client actually sent
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(asset, field, value)
    db.commit()
    db.refresh(asset)
    return asset


# -- DELETE -- admin only -----------------------------------------------------------


@router.delete("/{asset_id}", status_code=204)
def delete_asset(
    asset_id: int,
    member: AdminMember,
    db: Session = Depends(get_db),
):
    asset = db.scalar(
        select(Asset).where(Asset.id == asset_id, Asset.organization_id == member.organization_id)
    )
    if asset is None:
        raise HTTPException(status_code=404, detail="Asset not found")
    db.delete(asset)
    db.commit()
