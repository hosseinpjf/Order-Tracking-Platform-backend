from pydantic_settings import BaseSettings
from datetime import timedelta, time

class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    OPEN_TIME: time = time(7, 0)
    CLOSE_TIME: time = time(23, 0)

    ALLOWED_FOLDERS: list = ["products", "tables", "categories", "site_info"]
    ALLOWED_EXTENSIONS: list = ["jpg", "jpeg", "png", "webp"]
    ALLOWED_CONTENT_TYPES: list = ["image/jpg", "image/jpeg", "image/png", "image/webp"]
    MAX_FILE_SIZE: int = 5 * 1024 * 1024  # 5MB

    RESERVATION_DURATION: timedelta = timedelta(minutes=5)

    JOB_INTERVAL_SECONDS: int = 60

    class Config:
        env_file = ".env"

settings = Settings()