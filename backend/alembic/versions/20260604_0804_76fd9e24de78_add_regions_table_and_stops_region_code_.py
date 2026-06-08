"""add regions table and stops region_code fk

Revision ID: 76fd9e24de78
Revises: a1b2c3d4e5f6
Create Date: 2026-06-04 08:04:19.764917+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '76fd9e24de78'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'regions',
        sa.Column('iata_code', sa.VARCHAR(length=10), nullable=False),
        sa.Column('name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('airport_name', sa.VARCHAR(length=500), nullable=False),
        sa.Column('country', sa.VARCHAR(length=255), nullable=False),
        sa.Column('lat', sa.DECIMAL(precision=10, scale=7), nullable=False),
        sa.Column('lng', sa.DECIMAL(precision=10, scale=7), nullable=False),
        sa.PrimaryKeyConstraint('iata_code'),
    )
    # NOT VALID defers row-level checking — existing stops with region_code values
    # are not validated here. Run seed.py first, then validate via:
    #   ALTER TABLE stops VALIDATE CONSTRAINT fk_stops_region_code;
    op.execute(
        "ALTER TABLE stops ADD CONSTRAINT fk_stops_region_code "
        "FOREIGN KEY (region_code) REFERENCES regions (iata_code) "
        "ON DELETE SET NULL NOT VALID"
    )


def downgrade() -> None:
    op.drop_constraint('fk_stops_region_code', 'stops', type_='foreignkey')
    op.drop_table('regions')
