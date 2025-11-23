from typing import Any, Literal
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml

from utils.singletonmeta import SingletonMeta


# Paths
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
DOTENV_PATH = Path(__file__).parent.parent / ".env"

# Type aliases for better validation
LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


class Role(BaseModel):
    """Represents a Discord role configuration."""

    id: int


class RolesAccessor:
    """
    Provides attribute-style access to roles dictionary.
    Allows settings.roles.gamer instead of settings.roles['gamer'].
    """

    def __init__(self, roles: dict[str, Role]):
        self._roles = roles

    def __getattr__(self, item: str) -> Role:
        if item.startswith("_"):
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{item}'"
            )
        if item not in self._roles:
            raise AttributeError(f"Role '{item}' not found in configuration")
        return self._roles[item]

    def __getitem__(self, item: str) -> Role:
        return self._roles[item]

    def keys(self) -> list[str]:
        return list(self._roles.keys())


class FileSettings(BaseModel):
    """Settings loaded from config.yaml - the source of truth."""

    log_event_level: LogLevel = "DEBUG"
    log_issue_level: LogLevel = "WARNING"
    logs_path: Path = Path("logs/")
    main_guild: int = 0  # Placeholder
    roles: dict[str, Role] = {
        "lesHabitues": Role(id=0),
        "gamer": Role(id=0),
    }


class EnvSettings(BaseSettings):
    """Settings loaded from .env file - secrets only."""

    discord_token: str
    postgres_password: str
    postgres_user: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    postgres_scheme: str = "postgresql+asyncpg"

    model_config = SettingsConfigDict(env_file=DOTENV_PATH, extra="ignore")


class AppSettings(metaclass=SingletonMeta):
    """
    Application settings combining env and config file sources.
    This is the single source of truth for the application.
    Singleton pattern ensures settings are loaded only once.
    """

    def __init__(self):
        """Initialize settings by loading from env and config file."""
        self._env = EnvSettings()  # type: ignore[call-arg]
        config = load_or_init_config(CONFIG_PATH)
        self._config = config
        self._roles_accessor = RolesAccessor(config.roles)

    # Expose config fields
    @property
    def log_event_level(self) -> LogLevel:
        return self._config.log_event_level

    @property
    def log_issue_level(self) -> LogLevel:
        return self._config.log_issue_level

    @property
    def logs_path(self) -> Path:
        return self._config.logs_path

    @property
    def main_guild(self) -> int:
        return self._config.main_guild

    @property
    def roles(self) -> RolesAccessor:
        return self._roles_accessor

    # Expose env fields
    @property
    def discord_token(self) -> str:
        return self._env.discord_token

    @property
    def postgres_password(self) -> str:
        return self._env.postgres_password

    @property
    def postgres_user(self) -> str:
        return self._env.postgres_user

    @property
    def postgres_db(self) -> str:
        return self._env.postgres_db

    @property
    def postgres_host(self) -> str:
        return self._env.postgres_host

    @property
    def postgres_port(self) -> str:
        return self._env.postgres_port

    @property
    def postgres_scheme(self) -> str:
        return self._env.postgres_scheme

    @property
    def postgres_url(self) -> str:
        """Computed postgres connection URL."""
        return f"{self.postgres_scheme}://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    def reload_config(self) -> None:
        """
        Reload configuration from config.yaml.
        Note: Role changes require bot restart due to Discord command decorators.
        """
        self._config = load_or_init_config(CONFIG_PATH)
        self._roles_accessor = RolesAccessor(self._config.roles)


def deep_merge(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries, preferring values from updates.
    Base provides defaults for missing keys.
    """
    result = base.copy()
    for key, value in updates.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def write_yaml_with_comments(path: Path, data: dict[str, Any]) -> None:
    """
    Write YAML file in a clean format.
    """
    lines = []
    lines.append("# ZORSBOT Configuration File")
    lines.append(
        "# This file is auto-generated and synchronized with the Settings schema."
    )
    lines.append("")

    # Log levels
    lines.append(
        "# Log level for general events (TRACE, DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)"
    )
    lines.append(f"log_event_level: {data['log_event_level']}")
    lines.append("")
    lines.append("# Log level for issues and errors")
    lines.append(f"log_issue_level: {data['log_issue_level']}")
    lines.append("")

    # Logs path
    lines.append("# Directory for log files")
    logs_path = data["logs_path"]
    if isinstance(logs_path, Path):
        logs_path = str(logs_path)
    lines.append(f"logs_path: {logs_path}")
    lines.append("")

    # Main guild
    lines.append("# Discord server (guild) ID")
    main_guild = data["main_guild"]
    lines.append(f"main_guild: {main_guild}")
    lines.append("")

    # Roles
    lines.append("# Discord role IDs for bot functionality")
    lines.append("roles:")
    for role_name, role_data in data["roles"].items():
        role_id = role_data["id"] if isinstance(role_data, dict) else role_data.id
        lines.append(f"  {role_name}:")
        lines.append(f"    id: {role_id}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class ConfigurationError(Exception):
    """Raised when configuration is incomplete or invalid."""

    pass


def validate_config(config: FileSettings) -> list[str]:
    """
    Validate configuration for placeholder values.
    Returns list of validation errors.
    """
    errors = []

    # Check main_guild
    if config.main_guild == 0:
        errors.append("main_guild is not configured (value is 0)")

    # Check roles
    for role_name, role in config.roles.items():
        if role.id == 0:
            errors.append(f"Role '{role_name}' is not configured (id is 0)")

    return errors


def load_or_init_config(path: Path) -> FileSettings:
    """
    Load configuration from YAML file.
    If file doesn't exist or is incomplete, create/update it with defaults and placeholders,
    then raise ConfigurationError to prevent bot startup with invalid configuration.
    """
    # Create default settings
    default_settings = FileSettings()

    if not path.exists():
        # Create new config file with defaults
        path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml_with_comments(path, default_settings.model_dump())

        # Raise error - config file was just created with placeholders
        raise ConfigurationError(
            f"\n{'=' * 70}\n"
            f"CONFIGURATION ERROR\n"
            f"{'=' * 70}\n"
            f"Configuration file created at:\n  {path}\n\n"
            f"Please edit the file and replace placeholder values (0) with actual\n"
            f"configuration values, then restart the bot.\n"
            f"{'=' * 70}\n"
        )

    # Load existing config
    raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw_data is None:
        raw_data = {}

    # Merge with defaults (defaults provide missing keys)
    base_data = default_settings.model_dump()
    merged_data = deep_merge(base_data, raw_data)

    # Validate and parse
    config = FileSettings.model_validate(merged_data)

    # Check if new fields were added (schema changed)
    config_was_updated = merged_data != raw_data

    if config_was_updated:
        # Write updated config with placeholders
        write_yaml_with_comments(path, config.model_dump())

    # Validate configuration - check for placeholders
    validation_errors = validate_config(config)

    if validation_errors:
        error_msg = (
            f"\n{'=' * 70}\n"
            f"CONFIGURATION ERROR\n"
            f"{'=' * 70}\n"
            f"Configuration validation failed for:\n  {path}\n\n"
            f"The following fields have placeholder values and must be configured:\n"
        )
        for error in validation_errors:
            error_msg += f"  - {error}\n"

        if config_was_updated:
            error_msg += (
                f"\n{'=' * 70}\n"
                f"NOTE: New configuration fields were added to the config file.\n"
                f"Please review and update all placeholder values.\n"
                f"{'=' * 70}\n"
            )
        else:
            error_msg += (
                f"\n{'=' * 70}\n"
                f"Please edit the configuration file and set proper values,\n"
                f"then restart the bot.\n"
                f"{'=' * 70}\n"
            )

        raise ConfigurationError(error_msg)

    return config


# Proxy for lazy-loading settings with SingletonMeta
class _SettingsProxy:
    """
    Proxy for lazy-loading settings on first attribute access.
    AppSettings uses SingletonMeta, so only one instance is ever created.
    """

    _instance: AppSettings | None = None

    def _get_instance(self) -> AppSettings:
        """Get or create the singleton AppSettings instance."""
        if self._instance is None:
            self._instance = AppSettings()
        return self._instance

    def __getattr__(self, name: str):
        return getattr(self._get_instance(), name)

    def __repr__(self) -> str:
        return repr(self._get_instance())


# Global settings instance - single source of truth
# Lazy-loaded via proxy: AppSettings() called only on first attribute access
settings: AppSettings = _SettingsProxy()  # type: ignore[assignment]
