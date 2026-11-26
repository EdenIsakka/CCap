from functools import cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Lo único que necesita Alembic para migrar."""

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    database_url: str


class Settings(DatabaseSettings):
    debug: bool = False
    # URL donde la persona abre la PWA. Arma los redirect URI y el destino tras el login.
    app_url: str = "http://localhost:5173"
    # Firma la cookie temporal del flujo OAuth (state, nonce, PKCE).
    session_secret: str = Field(min_length=32)
    # Correos que pueden iniciar sesión, separados por coma. Vacío: nadie entra.
    allowed_emails: str = ""
    google_client_id: str = Field(min_length=1)
    google_client_secret: str = Field(min_length=1)

    def is_email_allowed(self, email: str) -> bool:
        allowed = {e.strip().lower() for e in self.allowed_emails.split(",") if e.strip()}
        return email.lower() in allowed


@cache
def get_settings() -> Settings:
    return Settings()
