from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    holded_api_key: str = Field(validation_alias="HOLDED_API_KEY")
    holded_base_url: str = Field(
        default="https://api.holded.com/api/invoicing/v1",
        validation_alias="HOLDED_BASE_URL",
    )
    holded_timeout_seconds: float = Field(default=20.0, validation_alias="HOLDED_TIMEOUT_SECONDS")

