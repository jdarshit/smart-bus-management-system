"""add student driver attendance modules

Revision ID: a4f1c7e2d9b3
Revises: 9b4d2f8c1a10
Create Date: 2026-03-15 22:05:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "a4f1c7e2d9b3"
down_revision = "9b4d2f8c1a10"
branch_labels = None
depends_on = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade():
    if not _table_exists("drivers"):
        op.create_table(
            "drivers",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("driver_name", sa.String(length=120), nullable=False),
            sa.Column("phone", sa.String(length=30), nullable=True),
            sa.Column("license_number", sa.String(length=80), nullable=False),
            sa.Column("bus_number", sa.String(length=50), nullable=False),
            sa.Column("photo", sa.String(length=255), nullable=True),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("license_number"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_drivers_license_number", "drivers", ["license_number"], unique=True)
        op.create_index("ix_drivers_bus_number", "drivers", ["bus_number"], unique=False)
        op.create_index("ix_drivers_user_id", "drivers", ["user_id"], unique=True)

    if not _table_exists("students"):
        op.create_table(
            "students",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("department", sa.String(length=120), nullable=False),
            sa.Column("year", sa.Integer(), nullable=False),
            sa.Column("bus_number", sa.String(length=50), nullable=False),
            sa.Column("pickup_stop", sa.String(length=150), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_students_bus_number", "students", ["bus_number"], unique=False)
        op.create_index("ix_students_pickup_stop", "students", ["pickup_stop"], unique=False)
        op.create_index("ix_students_user_id", "students", ["user_id"], unique=True)

    if not _table_exists("attendance"):
        op.create_table(
            "attendance",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("student_id", sa.Integer(), nullable=False),
            sa.Column("student_name", sa.String(length=120), nullable=False),
            sa.Column("bus_number", sa.String(length=50), nullable=False),
            sa.Column("pickup_stop", sa.String(length=150), nullable=False),
            sa.Column("date", sa.Date(), nullable=False),
            sa.Column("time", sa.Time(), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
            sa.UniqueConstraint("student_id", "date", name="uq_attendance_student_date"),
        )
        op.create_index("ix_attendance_student_id", "attendance", ["student_id"], unique=False)
        op.create_index("ix_attendance_bus_number", "attendance", ["bus_number"], unique=False)
        op.create_index("ix_attendance_pickup_stop", "attendance", ["pickup_stop"], unique=False)
        op.create_index("ix_attendance_date", "attendance", ["date"], unique=False)
        op.create_index("ix_attendance_status", "attendance", ["status"], unique=False)


def downgrade():
    if _table_exists("attendance"):
        op.drop_index("ix_attendance_status", table_name="attendance")
        op.drop_index("ix_attendance_date", table_name="attendance")
        op.drop_index("ix_attendance_pickup_stop", table_name="attendance")
        op.drop_index("ix_attendance_bus_number", table_name="attendance")
        op.drop_index("ix_attendance_student_id", table_name="attendance")
        op.drop_table("attendance")

    if _table_exists("students"):
        op.drop_index("ix_students_user_id", table_name="students")
        op.drop_index("ix_students_pickup_stop", table_name="students")
        op.drop_index("ix_students_bus_number", table_name="students")
        op.drop_table("students")

    if _table_exists("drivers"):
        op.drop_index("ix_drivers_user_id", table_name="drivers")
        op.drop_index("ix_drivers_bus_number", table_name="drivers")
        op.drop_index("ix_drivers_license_number", table_name="drivers")
        op.drop_table("drivers")
