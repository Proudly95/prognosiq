from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.routes import auth, orgs
from app.core.db import get_db

app = FastAPI(title="PrognosIQ API", version="0.1.0")
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(orgs.router, prefix="/orgs", tags=["organizations"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready(
    db: Session = Depends(get_db),
) -> dict[
    str,
    str,
]:
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "connected"}
