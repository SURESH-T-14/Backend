from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    start_location: Mapped[str] = mapped_column(String(200), nullable=False)
    end_location: Mapped[str] = mapped_column(String(200), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    points: Mapped[list["RoutePoint"]] = relationship(
        "RoutePoint", back_populates="route", cascade="all, delete-orphan", order_by="RoutePoint.sequence_index"
    )
    user: Mapped["User | None"] = relationship("User", back_populates="route", uselist=False)


class RoutePoint(Base):
    """One ordered waypoint of a route's polyline."""

    __tablename__ = "route_points"
    __table_args__ = (UniqueConstraint("route_id", "sequence_index", name="uq_route_points_route_sequence"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_index: Mapped[int] = mapped_column(Integer, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    route: Mapped["Route"] = relationship("Route", back_populates="points")
