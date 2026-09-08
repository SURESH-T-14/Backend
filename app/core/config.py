from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://gps_user:gps_password@localhost:5432/gps_tracking"

    jwt_secret_key: str = "dev-secret-key-do-not-use-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_pattern: str = "vehicles/+/location"

    vehicle_moving_speed_threshold_kmh: float = 3.0
    vehicle_offline_after_seconds: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
