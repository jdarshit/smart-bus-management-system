"""add fast rfid indexes

Revision ID: 9b4d2f8c1a10
Revises: 7e34e9a3dfbe
Create Date: 2026-03-15 20:40:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "9b4d2f8c1a10"
down_revision = "7e34e9a3dfbe"
branch_labels = None
depends_on = None


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes(table_name)
    return any(ix.get("name") == index_name for ix in indexes)


def upgrade():
    if not _index_exists("buses", "idx_bus_rfid"):
        op.create_index("idx_bus_rfid", "buses", ["rfid_uid"], unique=False)

    if not _index_exists("bus_arrival_logs", "idx_arrival_time"):
        op.create_index("idx_arrival_time", "bus_arrival_logs", ["arrival_time"], unique=False)


def downgrade():
    if _index_exists("bus_arrival_logs", "idx_arrival_time"):
        op.drop_index("idx_arrival_time", table_name="bus_arrival_logs")

    if _index_exists("buses", "idx_bus_rfid"):
        op.drop_index("idx_bus_rfid", table_name="buses")
