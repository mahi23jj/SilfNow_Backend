import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Talk Gym Backend")
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    api_v1_prefix: str = os.getenv("API_V1_PREFIX", "/api/v1")
    postgres_url: str | None = (
        os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or os.getenv("postgres_url")
    )
    secret_key: str = os.getenv("SECRET_KEY")
    algorithm: str = os.getenv("ALGORITHM")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    cloudinary_cloud_name: str = os.getenv("CLOUDINARY_Cloud_name")
    cloudinary_api_key: str = os.getenv("CLOUDINARY_Api_Key")
    cloudinary_api_secret: str = os.getenv("CLOUDINARY_Api_Secret")
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "10"))
    rate_limit_per_hour: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "100"))
    max_audio_size_bytes: int = int(
        os.getenv("MAX_AUDIO_SIZE_BYTES", str(10 * 1024 * 1024))
    )
    max_audio_duration_seconds: int = int(os.getenv("MAX_AUDIO_DURATION_SECONDS", "90"))
    daily_audio_upload_limit: int = int(os.getenv("DAILY_AUDIO_UPLOAD_LIMIT", "20"))
    redis_host: str = os.getenv("REDIS_HOST", "redis")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_username: str = os.getenv("REDIS_USERNAME")
    redis_password: str = os.getenv("REDIS_PASSWORD")
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID")


settings = Settings()
