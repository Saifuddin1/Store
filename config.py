import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 🔐 SECURITY
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    # =========================
    # DATABASE CONFIG
    # =========================

    # Render provides DATABASE_URL automatically (Postgres)
    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # Fix for SQLAlchemy + Render Postgres
        SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace(
            "postgres://", "postgresql://", 1
        )
    else:
        # Fallback (local MySQL)
        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{os.getenv('MYSQL_DB_USERNAME')}:"
            f"{os.getenv('MYSQL_DB_PASSWORD')}@"
            f"{os.getenv('MYSQL_DB_HOST')}:"
            f"{os.getenv('MYSQL_DB_PORT')}/"
            f"{os.getenv('MYSQL_DB_NAME')}?charset=utf8mb4"
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =========================
    # SAFE POOL SETTINGS
    # =========================
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }
