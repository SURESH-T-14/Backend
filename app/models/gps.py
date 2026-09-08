from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class GpsTracking(Base):
    __tablename__ = "gps_tracking"
    __table_args__ = (
        # Speeds up both "latest location" and "history in range" lookups per vehicle.
        Index("ix_gps_tracking_vehicle_id_timestamp", "vehicle_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    speed: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vehicle: Mapped["Vehicle"] = relationship("Vehicle", back_populates="gps_records")
