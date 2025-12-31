import os
from dotenv import load_dotenv

# Load .env locally (safe in prod too)
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # ======================================
    # DATABASE CONFIG (SAFE & EXPLICIT)
    # ======================================

    DATABASE_URL = os.getenv("DATABASE_URL")

    if DATABASE_URL:
        # Production / Heroku / Render / Railway
        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:
        # MySQL (Local or PythonAnywhere)
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
            f"mysql+pymysql://{MYSQL_DB_USERNAME}:{MYSQL_DB_PASSWORD}@"
            f"{MYSQL_DB_HOST}:{MYSQL_DB_PORT}/{MYSQL_DB_NAME}"
            "?charset=utf8mb4"
        )
