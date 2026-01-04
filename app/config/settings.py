from pydantic_settings import BaseSettings, SettingsConfigDict
import json
from typing import Optional


class Settings(BaseSettings):
    openai_api_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_base_url: Optional[str] = None
    email_address: Optional[str] = None
    google_calendar_credentials_json: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    def get_google_credentials_dict(self) -> dict:
        if not self.google_calendar_credentials_json:
            raise ValueError(
                "GOOGLE_CALENDAR_CREDENTIALS_JSON variable is not present in .env file"
            )
        return json.loads(self.google_calendar_credentials_json)


settings = Settings()
