import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _resolve_database_uri() -> str:
    """Resolve DATABASE_URL for Render/Heroku (PostgreSQL) or fallback to local SQLite."""
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        # Heroku & older Render configs may use legacy postgres:// scheme
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        return db_url

    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    return f"sqlite:///{instance_dir / 'lely45.db'}"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "lely45-retrospektyva-2026-dev-secret-key")
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size
    UPLOAD_FOLDER = str(BASE_DIR / "static" / "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

