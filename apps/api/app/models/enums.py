import enum

from sqlalchemy import Enum as SAEnum


class MemberRole(enum.StrEnum):
    ADMIN = "admin"
    AGENT = "agent"
    VIEWER = "viewer"


class AssetType(enum.StrEnum):
    PUMP = "pump"
    MOTOR = "motor"
    TURBOFAN = "turbofan"
    COMPRESSOR = "compressor"
    CONVEYOR = "conveyor"


class WorkOrderStatus(enum.StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"


class WorkOrderPriority(enum.StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class WorkOrderSource(enum.StrEnum):
    MANUAL = "manual"
    SENSOR_ALERT = "sensor_alert"


def enum_column(enum_cls):
    """Non-native enum: VARCHAR + CHECK constraint storing the *values*.

    Native PG enums are paintful to alter (add-value migration, no removal);
    text + check keeps changes to a one-line contraint swap.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        values_callable=lambda e: [m.value for m in e],
        length=50,
        create_constraint=True,
    )
