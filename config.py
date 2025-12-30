import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = "Saifuddin"
    MYSQL_DB_NAME = os.getenv('MYSQL_DB_NAME')
    MYSQL_DB_USERNAME = os.getenv('MYSQL_DB_USERNAME')
    MYSQL_DB_PASSWORD = os.getenv('MYSQL_DB_PASSWORD')
    MYSQL_DB_HOST = os.getenv('MYSQL_DB_HOST')
    MYSQL_DB_PORT = os.getenv('MYSQL_DB_PORT')
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 30,       # Default is 5, increase if needed
        "max_overflow": 50,    # Default is 10, allows extra temporary connections
        "pool_timeout": 60,    # Default is 30 seconds, increase if queries take longer
        "pool_pre_ping": True,
        "pool_recycle": 1800   # Recycle connections every 30 minutes
    }

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{MYSQL_DB_USERNAME}:{MYSQL_DB_PASSWORD}@"
        f"{MYSQL_DB_HOST}:{MYSQL_DB_PORT}/{MYSQL_DB_NAME}?charset=utf8mb4"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=365 * 10)
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = 'myFlaskApp_session:'

    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS') == 'True'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL') == 'True'
