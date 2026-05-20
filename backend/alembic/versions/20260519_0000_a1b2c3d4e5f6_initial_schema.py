"""initial schema

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-05-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a1b2c3d4e5f6"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── trips ─────────────────────────────────────────────────────────────────
    op.create_table(
        "trips",
        sa.Column("id", sa.VARCHAR(100), nullable=False),
        sa.Column("title", sa.VARCHAR(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_trips_start_end_date", "trips", ["start_date", "end_date"])

    # ── stops ─────────────────────────────────────────────────────────────────
    op.create_table(
        "stops",
        sa.Column("id", sa.VARCHAR(100), nullable=False),
        sa.Column("trip_id", sa.VARCHAR(100), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("location", sa.VARCHAR(500), nullable=False),
        sa.Column("lat", sa.Numeric(10, 7), nullable=True),
        sa.Column("lng", sa.Numeric(10, 7), nullable=True),
        sa.Column("status", sa.VARCHAR(20), nullable=False),
        sa.Column("region_code", sa.VARCHAR(10), nullable=True),
        sa.Column("post_type", sa.VARCHAR(20), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("status IN ('visited', 'planned')", name="ck_stops_status"),
        sa.CheckConstraint(
            "post_type IN ('instagram', 'substack', 'planned')",
            name="ck_stops_post_type",
        ),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stops_trip_date", "stops", ["trip_id", "date"])
    op.create_index("ix_stops_trip_status", "stops", ["trip_id", "status"])
    op.create_index("ix_stops_trip_region", "stops", ["trip_id", "region_code"])
    op.create_index("ix_stops_date", "stops", ["date"])

    # ── instagram_posts ───────────────────────────────────────────────────────
    op.create_table(
        "instagram_posts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("stop_id", sa.VARCHAR(100), nullable=False),
        sa.Column("instagram_id", sa.VARCHAR(100), nullable=False),
        sa.Column("shortcode", sa.VARCHAR(100), nullable=False),
        sa.Column("media_url", sa.VARCHAR(500), nullable=False),
        sa.Column("caption", sa.Text(), server_default="", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stop_id", name="uq_instagram_posts_stop_id"),
        sa.UniqueConstraint("instagram_id", name="uq_instagram_posts_instagram_id"),
    )
    op.create_index(
        "ix_instagram_posts_timestamp", "instagram_posts", ["timestamp"]
    )
    op.create_index("ix_instagram_posts_stop_id", "instagram_posts", ["stop_id"])

    # ── substack_posts ────────────────────────────────────────────────────────
    op.create_table(
        "substack_posts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("stop_id", sa.VARCHAR(100), nullable=True),
        sa.Column("substack_id", sa.VARCHAR(500), nullable=False),
        sa.Column("title", sa.VARCHAR(500), nullable=False),
        sa.Column("subtitle", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["stop_id"], ["stops.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("substack_id", name="uq_substack_posts_substack_id"),
    )
    op.create_index(
        "ix_substack_posts_published_at", "substack_posts", ["published_at"]
    )
    op.create_index("ix_substack_posts_stop_id", "substack_posts", ["stop_id"])


def downgrade() -> None:
    op.drop_table("substack_posts")
    op.drop_table("instagram_posts")
    op.drop_table("stops")
    op.drop_table("trips")
