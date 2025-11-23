from typing import Any, Literal
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


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


class AppSettings:
    """
    Application settings combining env and config file sources.
    This is the single source of truth for the application.
    """

    def __init__(self, env: EnvSettings, config: FileSettings):
        self._env = env
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

    @classmethod
    def load(cls) -> "AppSettings":
        """
        Load settings from environment and config file.
        Automatically syncs config.yaml to match the schema.
        """
        env = EnvSettings()  # type: ignore[call-arg]
        config = load_or_init_config(CONFIG_PATH)
        return cls(env, config)

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
    Write YAML file with helpful comments for placeholder values.
    """
    lines = []
    lines.append("# ZORSBOT Configuration File")
    lines.append(
        "# This file is auto-generated and synchronized with the Settings schema."
    )
    lines.append("# Replace placeholder values (0, <PLACEHOLDER>) with actual values.")
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
    main_guild = data["main_guild"]
    if main_guild == 0:
        lines.append("# TODO: Set your Discord server (guild) ID")
    lines.append(f"main_guild: {main_guild}")
    lines.append("")

    # Roles
    lines.append("# Discord role IDs for bot functionality")
    lines.append("roles:")
    for role_name, role_data in data["roles"].items():
        role_id = role_data["id"] if isinstance(role_data, dict) else role_data.id
        if role_id == 0:
            lines.append(f"  # TODO: Set the Discord role ID for {role_name}")
        lines.append(f"  {role_name}:")
        lines.append(f"    id: {role_id}")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_or_init_config(path: Path) -> FileSettings:
    """
    Load configuration from YAML file.
    If file doesn't exist or is incomplete, create/update it with defaults and placeholders.
    """
    # Create default settings
    default_settings = FileSettings()

    if not path.exists():
        # Create new config file with defaults
        path.parent.mkdir(parents=True, exist_ok=True)
        write_yaml_with_comments(path, default_settings.model_dump())
        return default_settings

    # Load existing config
    raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw_data is None:
        raw_data = {}

    # Merge with defaults (defaults provide missing keys)
    base_data = default_settings.model_dump()
    merged_data = deep_merge(base_data, raw_data)

    # Validate and parse
    config = FileSettings.model_validate(merged_data)

    # Update file if it was incomplete
    if merged_data != raw_data:
        write_yaml_with_comments(path, config.model_dump())

    return config


# Global settings instance - single source of truth
settings: AppSettings = AppSettings.load()
