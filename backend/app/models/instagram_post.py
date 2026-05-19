import uuid
from datetime import datetime

from sqlalchemy import TEXT, VARCHAR, ForeignKey, Index, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class InstagramPost(Base):
    __tablename__ = "instagram_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )
    stop_id: Mapped[str] = mapped_column(
        VARCHAR(100),
        ForeignKey("stops.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    instagram_id: Mapped[str] = mapped_column(VARCHAR(100), nullable=False, unique=True)
    shortcode: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    media_url: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    caption: Mapped[str] = mapped_column(TEXT, nullable=False, default="")
    timestamp: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    stop = relationship("Stop", back_populates="instagram_post")

    __table_args__ = (
        UniqueConstraint("instagram_id", name="uq_instagram_posts_instagram_id"),
        Index("ix_instagram_posts_timestamp", "timestamp"),
        Index("ix_instagram_posts_stop_id", "stop_id"),
    )
