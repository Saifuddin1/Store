import os
from datetime import timedelta
from dotenv import load_dotenv

# ==================================================
# Load .env ONLY for local development
# (PythonAnywhere env vars already exist)
# ==================================================
load_dotenv(override=False)

class Config:
    # ==================================================
    # BASIC FLASK CONFIG
    # ==================================================
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # ==================================================
    # DATABASE CONFIG (EXPLICIT & SAFE)
    # ==================================================

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL and DATABASE_URL.strip():
        # 🌍 Heroku / Render / Railway / Neon
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        # 🐬 MySQL (Local OR PythonAnywhere)
        MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
        MYSQL_DB_USERNAME = os.getenv("MYSQL_DB_USERNAME")
        MYSQL_DB_PASSWORD = os.getenv("MYSQL_DB_PASSWORD")
        MYSQL_DB_HOST = os.getenv("MYSQL_DB_HOST")
        MYSQL_DB_PORT = os.getenv("MYSQL_DB_PORT", "3306")

        if not all([
            MYSQL_DB_NAME,
            MYSQL_DB_USERNAME,
            MYSQL_DB_PASSWORD,
            MYSQL_DB_HOST,
        ]):
            raise RuntimeError(
                "❌ MySQL environment variables are missing. "
                "Check MYSQL_DB_* settings."
            )

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_DB_USERNAME}:"
            f"{MYSQL_DB_PASSWORD}@"
            f"{MYSQL_DB_HOST}:"
            f"{MYSQL_DB_PORT}/"
            f"{MYSQL_DB_NAME}"
            "?charset=utf8mb4"
        )

    # ==================================================
    # MAIL CONFIG
    # ==================================================
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "0") or 0)
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "False") == "True"
    MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", "False") == "True"
