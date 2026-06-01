import uuid
from datetime import datetime

from sqlalchemy import TEXT, VARCHAR, ForeignKey, Index, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


class SubstackPost(Base):
    __tablename__ = "substack_posts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=sa_text("gen_random_uuid()"),
    )
    stop_id: Mapped[str | None] = mapped_column(
        VARCHAR(100),
        ForeignKey("stops.id", ondelete="SET NULL"),
        nullable=True,
    )
    substack_id: Mapped[str] = mapped_column(VARCHAR(500), nullable=False, unique=True)
    title: Mapped[str] = mapped_column(VARCHAR(500), nullable=False)
    subtitle: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    body: Mapped[str] = mapped_column(TEXT, nullable=False)
    published_at: Mapped[datetime] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )

    stop = relationship("Stop", back_populates="substack_post")

    __table_args__ = (
        UniqueConstraint("substack_id", name="uq_substack_posts_substack_id"),
        Index("ix_substack_posts_published_at", "published_at"),
        Index("ix_substack_posts_stop_id", "stop_id"),
    )
