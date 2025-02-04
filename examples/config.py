from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str

    yandex_client_id: str
    yandex_client_secret: str

    telegram_bot_username: str
    telegram_bot_token: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
