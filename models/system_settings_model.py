from models import db


class SystemSettings(db.Model):
    __tablename__ = "system_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    active_shift = db.Column(db.String(20), nullable=False, default="shift1")

    @staticmethod
    def get_singleton() -> "SystemSettings":
        row = SystemSettings.query.first()
        if row is None:
            row = SystemSettings(active_shift="shift1")
            db.session.add(row)
            db.session.commit()
        return row
