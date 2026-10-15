from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import hash_password
from app.models import User
from app.schemas.user import UserCreate, UserRead

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    try:
        hashed = hash_password(user_in.password)
        user = User(
            email=user_in.email,
            full_name=user_in.full_name,
            password_hash=hashed,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Email already registered") from None
    return user
