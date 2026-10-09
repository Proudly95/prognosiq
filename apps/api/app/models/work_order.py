from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.enums import WorkOrderPriority, WorkOrderSource, WorkOrderStatus, enum_column


class WorkOrder(Base):
    __tablename__ = "work_orders"
    __table_args__ = (
        Index("ix_work_orders_organization_id_status", "organization_id", "status"),
        Index("ix_work_orders_asset_id", "asset_id"),
        Index("ix_work_orders_assignee_id", "assignee_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    organization_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("organizations.id"), nullable=False
    )
    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="RESTRICT"), nullable=False
    )
    assignee_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    created_by_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[WorkOrderStatus] = mapped_column(
        enum_column(WorkOrderStatus), nullable=False, default=WorkOrderStatus.OPEN
    )
    priority: Mapped[WorkOrderPriority] = mapped_column(
        enum_column(WorkOrderPriority), nullable=False, default=WorkOrderPriority.NORMAL
    )
    category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[WorkOrderSource] = mapped_column(enum_column(WorkOrderSource), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
