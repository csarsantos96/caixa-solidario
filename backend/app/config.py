from pathlib import Path
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=Path(__file__).resolve().parents[2] / ".env", extra="ignore")
    database_url: str = "sqlite:///./caixa.db"
    admin_username: str = "admin"
    admin_password: SecretStr
    cookie_secure: bool = False
    session_hours: int = Field(default=12, ge=1, le=72)
    resend_api_key: SecretStr = SecretStr("")
    receipt_from: str = ""

    def validate_password(self):
        value = self.admin_password.get_secret_value()
        if len(value) < 12 or value.startswith("CHANGE_ME"):
            raise ValueError("Configure ADMIN_PASSWORD com pelo menos 12 caracteres. Use scripts/configure.py.")
