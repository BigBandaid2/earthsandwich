from datetime import date, datetime

from sqlalchemy import DATE, TEXT, VARCHAR, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(VARCHAR(100), primary_key=True)
    title: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    description: Mapped[str] = mapped_column(TEXT, nullable=False)
    start_date: Mapped[date] = mapped_column(DATE, nullable=False)
    end_date: Mapped[date] = mapped_column(DATE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    stops = relationship("Stop", back_populates="trip", order_by="Stop.sequence_order")

    __table_args__ = (
        Index("ix_trips_start_end_date", "start_date", "end_date"),
    )
