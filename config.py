import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Connection pool (safe for prod)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 1800,
    }

    # 🔀 DATABASE SWITCH (Postgres > MySQL fallback)
    if os.getenv("DATABASE_URL"):
        
        SQLALCHEMY_DATABASE_URI = os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://root:password@localhost/store"
        )
    else:
        # Local MySQL
        MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
        MYSQL_DB_USERNAME = os.getenv("MYSQL_DB_USERNAME")
        MYSQL_DB_PASSWORD = os.getenv("MYSQL_DB_PASSWORD")
        MYSQL_DB_HOST = os.getenv("MYSQL_DB_HOST", "localhost")
        MYSQL_DB_PORT = os.getenv("MYSQL_DB_PORT", "3306")

        SQLALCHEMY_DATABASE_URI = (
            f"mysql+pymysql://{MYSQL_DB_USERNAME}:{MYSQL_DB_PASSWORD}@"
            f"{MYSQL_DB_HOST}:{MYSQL_DB_PORT}/{MYSQL_DB_NAME}?charset=utf8mb4"
        )
