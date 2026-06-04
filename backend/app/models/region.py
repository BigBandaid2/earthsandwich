from sqlalchemy import DECIMAL, VARCHAR
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Region(Base):
    __tablename__ = "regions"

    iata_code: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True)
    name: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    airport_name: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    country: Mapped[str] = mapped_column(VARCHAR(255), nullable=False)
    lat: Mapped[float] = mapped_column(DECIMAL(10, 7), nullable=False)
    lng: Mapped[float] = mapped_column(DECIMAL(10, 7), nullable=False)
