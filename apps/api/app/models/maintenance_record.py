from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

if TYPE_CHECKING:
    from app.models.asset import Asset


class MaintenanceRecord(Base):
    __tablename__ = "maintenance_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id"), nullable=False, index=True
    )
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    asset: Mapped["Asset"] = relationship(back_populates="maintenance_records")
