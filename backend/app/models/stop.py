from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DATE, TEXT, VARCHAR, CheckConstraint, ForeignKey, Index
from sqlalchemy import DECIMAL as SA_DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Stop(Base):
    __tablename__ = "stops"

    id: Mapped[str] = mapped_column(VARCHAR(100), primary_key=True)
    trip_id: Mapped[str] = mapped_column(
        VARCHAR(100), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False
    )
    date: Mapped[date] = mapped_column(DATE, nullable=False)
    location: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    lat: Mapped[Decimal | None] = mapped_column(SA_DECIMAL(10, 7), nullable=True)
    lng: Mapped[Decimal | None] = mapped_column(SA_DECIMAL(10, 7), nullable=True)
    status: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    region_code: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    post_type: Mapped[str] = mapped_column(VARCHAR(20), nullable=False)
    caption: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    trip = relationship("Trip", back_populates="stops")
    instagram_post = relationship(
        "InstagramPost", back_populates="stop", uselist=False
    )
    substack_post = relationship(
        "SubstackPost", back_populates="stop", uselist=False
    )

    __table_args__ = (
        CheckConstraint("status IN ('visited', 'planned')", name="ck_stops_status"),
        CheckConstraint(
            "post_type IN ('instagram', 'substack', 'planned')",
            name="ck_stops_post_type",
        ),
        Index("ix_stops_trip_date", "trip_id", "date"),
        Index("ix_stops_trip_status", "trip_id", "status"),
        Index("ix_stops_trip_region", "trip_id", "region_code"),
        Index("ix_stops_date", "date"),
    )
