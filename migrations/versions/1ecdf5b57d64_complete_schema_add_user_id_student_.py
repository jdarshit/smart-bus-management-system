"""complete schema - add user_id, student_name, year, pickup_point, driver_name, phone, license_number, route_name, capacity, approved fields

Revision ID: 1ecdf5b57d64
Revises: 243bda9430d1
Create Date: 2026-03-12 17:22:48.904189

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1ecdf5b57d64"
down_revision = "243bda9430d1"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # BUSES: columns already added in partial run; only fix index + FK
    conn.execute(sa.text("ALTER TABLE buses DROP FOREIGN KEY buses_ibfk_1"))
    conn.execute(sa.text("ALTER TABLE buses DROP INDEX driver_id"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_buses_driver_id ON buses (driver_id)"))
    conn.execute(sa.text("ALTER TABLE buses ADD CONSTRAINT buses_driver_fk FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE SET NULL"))

    # DRIVERS: add all missing columns
    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN user_id INT NULL"))
    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN driver_name VARCHAR(100) NOT NULL DEFAULT ''"))
    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN phone VARCHAR(20) NULL"))
    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN license_number VARCHAR(50) NULL"))
    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN created_at DATETIME NOT NULL DEFAULT NOW()"))
    conn.execute(sa.text("CREATE INDEX ix_drivers_user_id ON drivers (user_id)"))
    conn.execute(sa.text("ALTER TABLE drivers ADD UNIQUE KEY uq_drivers_license (license_number)"))
    conn.execute(sa.text("ALTER TABLE drivers ADD CONSTRAINT drivers_user_fk FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN name"))

    # MILEAGE LOGS: add approved + refresh FK/indexes
    conn.execute(sa.text("ALTER TABLE mileage_logs ADD COLUMN approved TINYINT(1) NOT NULL DEFAULT 0"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP FOREIGN KEY mileage_logs_ibfk_1"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP FOREIGN KEY mileage_logs_ibfk_2"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP INDEX bus_id"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP INDEX driver_id"))
    conn.execute(sa.text("CREATE INDEX ix_mileage_logs_driver_id ON mileage_logs (driver_id)"))
    conn.execute(sa.text("CREATE INDEX ix_mileage_logs_bus_id ON mileage_logs (bus_id)"))
    conn.execute(sa.text("CREATE INDEX ix_mileage_logs_date ON mileage_logs (date)"))
    conn.execute(sa.text("ALTER TABLE mileage_logs ADD CONSTRAINT ml_driver_fk FOREIGN KEY (driver_id) REFERENCES drivers (id) ON DELETE CASCADE"))
    conn.execute(sa.text("ALTER TABLE mileage_logs ADD CONSTRAINT ml_bus_fk FOREIGN KEY (bus_id) REFERENCES buses (id) ON DELETE CASCADE"))

    # STUDENTS: add all missing columns
    conn.execute(sa.text("ALTER TABLE students ADD COLUMN user_id INT NULL"))
    conn.execute(sa.text("ALTER TABLE students ADD COLUMN student_name VARCHAR(100) NOT NULL DEFAULT ''"))
    conn.execute(sa.text("ALTER TABLE students ADD COLUMN year INT NULL"))
    conn.execute(sa.text("ALTER TABLE students ADD COLUMN pickup_point VARCHAR(150) NULL"))
    conn.execute(sa.text("ALTER TABLE students ADD COLUMN created_at DATETIME NOT NULL DEFAULT NOW()"))
    conn.execute(sa.text("ALTER TABLE students DROP FOREIGN KEY students_ibfk_1"))
    conn.execute(sa.text("ALTER TABLE students DROP INDEX bus_id"))
    conn.execute(sa.text("CREATE INDEX ix_students_user_id ON students (user_id)"))
    conn.execute(sa.text("CREATE INDEX ix_students_bus_id ON students (bus_id)"))
    conn.execute(sa.text("ALTER TABLE students ADD CONSTRAINT students_user_fk FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL"))
    conn.execute(sa.text("ALTER TABLE students ADD CONSTRAINT students_bus_fk FOREIGN KEY (bus_id) REFERENCES buses (id) ON DELETE SET NULL"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN name"))

    # USERS: rename email index
    conn.execute(sa.text("ALTER TABLE users DROP INDEX email"))
    conn.execute(sa.text("CREATE UNIQUE INDEX ix_users_email ON users (email)"))


def downgrade():
    conn = op.get_bind()

    conn.execute(sa.text("ALTER TABLE users DROP INDEX ix_users_email"))
    conn.execute(sa.text("CREATE UNIQUE INDEX email ON users (email)"))

    conn.execute(sa.text("ALTER TABLE students ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT ''"))
    conn.execute(sa.text("ALTER TABLE students DROP FOREIGN KEY students_bus_fk"))
    conn.execute(sa.text("ALTER TABLE students DROP FOREIGN KEY students_user_fk"))
    conn.execute(sa.text("ALTER TABLE students DROP INDEX ix_students_bus_id"))
    conn.execute(sa.text("ALTER TABLE students DROP INDEX ix_students_user_id"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN created_at"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN pickup_point"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN year"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN student_name"))
    conn.execute(sa.text("ALTER TABLE students DROP COLUMN user_id"))
    conn.execute(sa.text("CREATE INDEX bus_id ON students (bus_id)"))
    conn.execute(sa.text("ALTER TABLE students ADD CONSTRAINT students_ibfk_1 FOREIGN KEY (bus_id) REFERENCES buses (id)"))

    conn.execute(sa.text("ALTER TABLE mileage_logs DROP FOREIGN KEY ml_driver_fk"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP FOREIGN KEY ml_bus_fk"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP INDEX ix_mileage_logs_driver_id"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP INDEX ix_mileage_logs_bus_id"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP INDEX ix_mileage_logs_date"))
    conn.execute(sa.text("ALTER TABLE mileage_logs DROP COLUMN approved"))
    conn.execute(sa.text("CREATE INDEX bus_id ON mileage_logs (bus_id)"))
    conn.execute(sa.text("CREATE INDEX driver_id ON mileage_logs (driver_id)"))
    conn.execute(sa.text("ALTER TABLE mileage_logs ADD CONSTRAINT mileage_logs_ibfk_1 FOREIGN KEY (bus_id) REFERENCES buses (id)"))
    conn.execute(sa.text("ALTER TABLE mileage_logs ADD CONSTRAINT mileage_logs_ibfk_2 FOREIGN KEY (driver_id) REFERENCES drivers (id)"))

    conn.execute(sa.text("ALTER TABLE drivers ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT ''"))
    conn.execute(sa.text("ALTER TABLE drivers DROP FOREIGN KEY drivers_user_fk"))
    conn.execute(sa.text("ALTER TABLE drivers DROP INDEX uq_drivers_license"))
    conn.execute(sa.text("ALTER TABLE drivers DROP INDEX ix_drivers_user_id"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN created_at"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN license_number"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN phone"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN driver_name"))
    conn.execute(sa.text("ALTER TABLE drivers DROP COLUMN user_id"))

    conn.execute(sa.text("ALTER TABLE buses DROP FOREIGN KEY buses_driver_fk"))
    conn.execute(sa.text("ALTER TABLE buses DROP INDEX ix_buses_driver_id"))
    conn.execute(sa.text("CREATE UNIQUE INDEX driver_id ON buses (driver_id)"))
    conn.execute(sa.text("ALTER TABLE buses ADD CONSTRAINT buses_ibfk_1 FOREIGN KEY (driver_id) REFERENCES drivers (id)"))
