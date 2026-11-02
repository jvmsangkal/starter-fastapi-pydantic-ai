from typing import Literal

from pydantic import SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    DATABASE_URL: str = 'sqlite:///./app.db'
    # Optional so the app boots without it; POST /chat needs it to call the model.
    OPENAI_API_KEY: SecretStr | None = None
    LOG_LEVEL: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'] = 'INFO'

    @field_validator('OPENAI_API_KEY')
    @classmethod
    def _check_api_key(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value().strip():
            raise ValueError('must not be empty (leave it unset instead)')
        return value

    @field_validator('DATABASE_URL')
    @classmethod
    def _check_database_url(cls, value: str) -> str:
        try:
            make_url(value)
        except ArgumentError, ValueError:
            # Don't echo the value: database URLs often embed a password.
            raise ValueError('not a valid SQLAlchemy database URL') from None
        return value


def load_env() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        problems = '\n'.join(
            f'  {".".join(map(str, error["loc"]))}: {error["msg"]}'
            for error in exc.errors(include_url=False)
        )
        raise SystemExit(
            f'Invalid environment variables:\n{problems}\nSee .env.example.'
        ) from None


env = load_env()
