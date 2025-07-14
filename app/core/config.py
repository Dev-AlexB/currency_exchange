from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class JWTSettings(BaseModel):
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRES_MINUTES: int


class CurrencySettings(BaseModel):
    API_KEY: str
    URL_LIST: str
    URL_EXCHANGE: str


class DatabaseSettings(BaseModel):
    URL: str


class Settings(BaseSettings):
    JWT: JWTSettings
    CURRENCY: CurrencySettings
    DATABASE: DatabaseSettings

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
    )


settings = Settings()
