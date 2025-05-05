from pathlib import Path
from enum import Enum
import warnings
from typing_extensions import Self
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, Field
from typing import Optional

from dotenv import load_dotenv
load_dotenv()


class Environment(str, Enum):
    local = "local"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path('.env').absolute(),
        env_ignore_empty=True,
        extra="ignore",
    )

    ENVIRONMENT: Environment
    PROJECT_NAME: str
    FRONTEND_HOST: str
    API_V1_STR: str
    MONGO_URL: str
    ROCKET_API_TOKEN: str
    SCRAPE: bool = True
    MAX_PAGES: int= 5
    COUNT_PER_PAGE: int = 10
    RUN_INTERVAL_PER_MINUTE: int

    DEFAULT_FRONTEND: Optional[str] = Field(default=None)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("FRONTEND_HOST", self.FRONTEND_HOST)
        self._check_default_secret("ENVIRONMENT", self.ENVIRONMENT)
        self._check_default_secret("PROJECT_NAME", self.PROJECT_NAME)
        self._check_default_secret("API_V1_STR", self.API_V1_STR)
        self._check_default_secret("MONGO_URL", self.MONGO_URL)
        self._check_default_secret("ROCKET_API_TOKEN", self.ROCKET_API_TOKEN)
        self._check_default_secret("SCRAPE", self.SCRAPE)
        self._check_default_secret("MAX_PAGES", self.MAX_PAGES)
        self._check_default_secret("COUNT_PER_PAGE", self.COUNT_PER_PAGE)
        self._check_default_secret("RUN_INTERVAL_PER_MINUTE", self.RUN_INTERVAL_PER_MINUTE)

        return self


settings = Settings()
