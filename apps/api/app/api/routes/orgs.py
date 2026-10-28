from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.routes.auth import get_current_user
from app.core.db import get_db
from app.models import Organization, OrganizationMember, User
from app.models.enums import MemberRole
from app.schemas.org import MemberAdd, MemberRead, OrganizationCreate, OrganizationRead

router = APIRouter(tags=["organizations"])


def get_current_org_member(
    org_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationMember:
    member = (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == org_id,
            OrganizationMember.user_id == current_user.id,
        )
        .first()
    )
    if member is None:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return member


def require_role(*roles: MemberRole):
    def checker(
        member: OrganizationMember = Depends(get_current_org_member),
    ) -> OrganizationMember:
        if member.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return member

    return checker


# Reusable dependency: "the current member must be an ADMIN of this org"
AdminMember = Annotated[OrganizationMember, Depends(require_role(MemberRole.ADMIN))]


@router.post("", response_model=OrganizationRead, status_code=201)
def create_org(
    org_in: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    org = Organization(name=org_in.name)
    db.add(org)
    db.flush()  # writes to the DB without committing
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=current_user.id,
        role=MemberRole.ADMIN,
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    return org


@router.get("", response_model=list[OrganizationRead])
def list_my_orgs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Organization)
        .join(OrganizationMember, OrganizationMember.organization_id == Organization.id)
        .filter(OrganizationMember.user_id == current_user.id)
        .all()
    )


@router.get("/{org_id}/members", response_model=list[MemberRead])
def list_members(
    member: OrganizationMember = Depends(get_current_org_member), db: Session = Depends(get_db)
):
    rows = (
        db.query(OrganizationMember, User)
        .join(User, OrganizationMember.user_id == User.id)
        .filter(OrganizationMember.organization_id == member.organization_id)
        .all()
    )
    return [
        MemberRead(
            id=m.id,
            user_id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=m.role,
            created_at=m.created_at,
        )
        for m, u in rows
    ]


@router.post("/{org_id}/members", response_model=MemberRead, status_code=201)
def add_member(
    body: MemberAdd,
    member: AdminMember,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        new_membership = OrganizationMember(
            organization_id=member.organization_id,
            user_id=user.id,
            role=body.role,
        )
        db.add(new_membership)
        db.commit()
        db.refresh(new_membership)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User is already a member") from None

    return MemberRead(
        id=new_membership.id,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=new_membership.role,
        created_at=new_membership.created_at,
    )
