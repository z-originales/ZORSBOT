from pathlib import Path
from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


# Paths
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
DOTENV_PATH = Path(__file__).parent.parent / ".env"


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class Role(BaseModel):
    """Discord role configuration."""

    id: int


class FileSettings(BaseModel):
    """Settings from config.yaml."""

    log_event_level: str = "DEBUG"
    log_issue_level: str = "WARNING"
    logs_path: Path = Path("logs/")
    main_guild: int = 0
    roles: dict[str, Role] = {
        "lesHabitues": Role(id=0),
        "gamer": Role(id=0),
    }

    @field_validator("main_guild")
    @classmethod
    def validate_main_guild(cls, v: int) -> int:
        if v == 0:
            raise ValueError("main_guild must be configured (cannot be 0)")
        return v

    @field_validator("roles")
    @classmethod
    def validate_roles(cls, v: dict[str, Role]) -> dict[str, Role]:
        for name, role in v.items():
            if role.id == 0:
                raise ValueError(f"Role '{name}' must be configured (id cannot be 0)")
        return v


class EnvSettings(BaseSettings):
    """Settings from .env - secrets only."""

    discord_token: str
    postgres_password: str
    postgres_user: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    postgres_scheme: str = "postgresql+asyncpg"

    model_config = SettingsConfigDict(env_file=DOTENV_PATH, extra="ignore")

    @property
    def postgres_url(self) -> str:
        """Computed postgres connection URL."""
        return f"{self.postgres_scheme}://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


class AppSettings(BaseModel):
    """
    Application settings combining env and config file.
    Simple Pydantic models, no magic.

    Access config via: settings.config.main_guild, settings.config.roles
    Access env via: settings.env.discord_token, settings.env.postgres_url
    """

    env: EnvSettings
    config: FileSettings

    @classmethod
    def load(cls) -> "AppSettings":
        """Load settings from .env and config.yaml."""
        # Load env
        env = EnvSettings()  # type: ignore[call-arg]

        # Load or create config
        if not CONFIG_PATH.exists():
            CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            default = FileSettings()
            CONFIG_PATH.write_text(
                yaml.dump(default.model_dump(), default_flow_style=False)
            )
            raise ConfigurationError(
                f"\n{'=' * 70}\n"
                f"Configuration file created at: {CONFIG_PATH}\n"
                f"Please configure it with your Discord server/role IDs.\n"
                f"{'=' * 70}\n"
            )

        # Load and validate config
        try:
            data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
            config = FileSettings.model_validate(data)
        except ValueError as e:
            raise ConfigurationError(
                f"\n{'=' * 70}\n"
                f"CONFIGURATION ERROR\n"
                f"{'=' * 70}\n"
                f"Configuration validation failed for: {CONFIG_PATH}\n\n"
                f"{str(e)}\n\n"
                f"{'=' * 70}\n"
                f"Please edit the config file and set proper values.\n"
                f"{'=' * 70}\n"
            ) from e

        return cls(env=env, config=config)


# Lazy-loading singleton
_settings: AppSettings | None = None


class _SettingsProxy:
    """Simple proxy to defer settings loading until first access."""

    def __getattr__(self, name: str):
        global _settings
        if _settings is None:
            _settings = AppSettings.load()
        return getattr(_settings, name)


# Global settings instance - loaded lazily on first access
settings: AppSettings = _SettingsProxy()  # type: ignore
