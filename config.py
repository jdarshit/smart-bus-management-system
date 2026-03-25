from urllib.parse import quote_plus
import os

from dotenv import load_dotenv

load_dotenv(override=True)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


def _normalize_database_url(url: str | None) -> str | None:
    if not url:
        return None
    normalized = url.strip()
    if normalized.startswith("mysql://"):
        normalized = normalized.replace("mysql://", "mysql+pymysql://", 1)
    return normalized


def _build_local_mysql_uri() -> str:
    mysql_host = os.getenv("MYSQL_HOST", "localhost")
    mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user = os.getenv("MYSQL_USER", "root")
    mysql_password = os.getenv("MYSQL_PASSWORD", "")
    mysql_db = os.getenv("MYSQL_DB", "smart_bus_db")
    return (
        f"mysql+pymysql://{mysql_user}:{quote_plus(mysql_password)}@"
        f"{mysql_host}:{mysql_port}/{mysql_db}"
    )


class Config:
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = False
    TESTING = False

    SECRET_KEY = os.getenv("SECRET_KEY", "")

    SQLALCHEMY_DATABASE_URI = _normalize_database_url(os.getenv("DATABASE_URL")) or _build_local_mysql_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = _env_int("MAIL_PORT", 587)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = _env_bool("MAIL_USE_TLS", True)
    MAIL_USE_SSL = _env_bool("MAIL_USE_SSL", False)
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME

    BUS_ARRIVAL_CUTOFF_HOUR = _env_int("BUS_ARRIVAL_CUTOFF_HOUR", 9)
    BUS_ARRIVAL_CUTOFF_MINUTE = _env_int("BUS_ARRIVAL_CUTOFF_MINUTE", 10)
    BUS_ARRIVAL_DEBOUNCE_SECONDS = _env_int("BUS_ARRIVAL_DEBOUNCE_SECONDS", 15)

    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join("uploads", "mileage"))
    ALLOWED_EXTENSIONS = {
        ext.strip().lower()
        for ext in os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg,gif,pdf").split(",")
        if ext.strip()
    }
    MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    PERMANENT_SESSION_LIFETIME_SECONDS = _env_int("PERMANENT_SESSION_LIFETIME_SECONDS", 7200)

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    @classmethod
    def validate(cls) -> None:
        if cls.ENV == "production":
            if not cls.SECRET_KEY or len(cls.SECRET_KEY) < 24:
                raise RuntimeError("SECRET_KEY must be set to a strong value in production.")


class DevelopmentConfig(Config):
    ENV = "development"
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "smartbus-dev-secret-key")


class ProductionConfig(Config):
    ENV = "production"
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_config_class():
    if os.getenv("FLASK_ENV", "development").lower() == "production":
        return ProductionConfig
    return DevelopmentConfig
