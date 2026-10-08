from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.db import get_db

app = FastAPI(title="PrognosIQ API", version="0.1.0")


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
