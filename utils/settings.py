from pathlib import Path
from typing import Literal

import yaml
from pydantic import (
    BaseModel,
    PostgresDsn,
    SecretStr,
    ValidationError,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_core import PydanticUndefined
from pydantic_settings import BaseSettings, SettingsConfigDict

# Paths
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.yaml"
DOTENV_PATH = Path(__file__).parent.parent / ".env"


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""

    pass


class Role(BaseModel):
    """Discord role configuration."""

    id: int


class Roles(BaseModel):
    """Typed roles configuration for type checking and autocomplete."""

    lesHabitues: Role
    gamer: Role

    @model_validator(mode="after")
    def validate_all_roles(self) -> "Roles":
        """Validate that all role IDs are configured (not 0)."""
        errors = []
        for field_name, field_value in self.__dict__.items():
            if isinstance(field_value, Role) and field_value.id == 0:
                errors.append(f"{field_name} role ID must be configured (cannot be 0)")

        if errors:
            raise ValueError("; ".join(errors))
        return self


class FileSettings(BaseModel):
    """Settings from config.yaml."""

    log_event_level: Literal["TRACE", "DEBUG", "INFO"] = "DEBUG"
    log_issue_level: Literal["WARNING", "ERROR", "CRITICAL"] = "WARNING"
    logs_path: Path = Path("logs/")
    main_guild: int
    roles: Roles

    @field_validator("main_guild")
    @classmethod
    def validate_main_guild(cls, v: int) -> int:
        if v == 0:
            raise ValueError("main_guild must be configured (cannot be 0)")
        return v


class EnvSettings(BaseSettings):
    """Settings from .env - secrets only."""

    discord_token: SecretStr
    postgres_password: SecretStr
    postgres_user: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    postgres_scheme: str = "postgresql+asyncpg"

    model_config = SettingsConfigDict(env_file=DOTENV_PATH, extra="ignore")

    @computed_field  # type: ignore
    @property
    def postgres_url(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme=self.postgres_scheme,
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=int(self.postgres_port),
            path=f"/{self.postgres_db}",
        )


class AppSettings(BaseModel):
    """
    Application settings combining env and config file.
    Simple Pydantic models, no magic.

    Access via: settings.config.main_guild, settings.config.roles
    Access via: settings.env.discord_token, settings.env.postgres_url
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
            template = cls._generate_config_template({})
            CONFIG_PATH.write_text(template)
            raise ConfigurationError(
                f"Configuration file created at: {CONFIG_PATH}\n"
                f"Please edit and configure required values."
            )

        # Load and validate config
        data = yaml.safe_load(CONFIG_PATH.read_text()) or {}
        try:
            config = FileSettings.model_validate(data)
        except ValidationError as e:
            # Check if it's a missing field error or validation error
            is_missing_field = any(error["type"] == "missing" for error in e.errors())

            if is_missing_field:
                # Missing fields - try to update the file
                template = cls._generate_config_template(data)
                try:
                    CONFIG_PATH.write_text(template)
                    raise ConfigurationError(
                        f"Configuration validation failed: {CONFIG_PATH}\n"
                        f"Missing fields have been added - please review and configure."
                    )
                except (OSError, PermissionError):
                    raise ConfigurationError(
                        f"Configuration validation failed: {CONFIG_PATH}\n"
                        f"File is read-only. Please update it manually with all required fields."
                    )
            else:
                # Validation error (e.g., invalid values)
                # Extract clean error messages
                errors: list[str] = []
                for error in e.errors():
                    field = ".".join(str(loc) for loc in error["loc"])
                    msg = error["msg"]
                    errors.append(f"  - {field}: {msg}")

                raise ConfigurationError(
                    f"Configuration validation failed: {CONFIG_PATH}\n"
                    f"Please fix the following errors:\n" + "\n".join(errors)
                )

        return cls(env=env, config=config)

    @staticmethod
    def _generate_config_template(existing_data: dict) -> str:
        """
        Generate config.yaml by merging existing data with schema defaults.
        Uses Pydantic model schema as single source of truth.
        """

        def deep_merge(base: dict, overlay: dict) -> dict:
            """Recursively merge overlay into base, preserving overlay values."""
            result = base.copy()
            for key, value in overlay.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        def schema_to_dict(model_class) -> dict:
            """
            Convert Pydantic model schema to dict with placeholder values.
            Recursively processes nested BaseModels.
            """
            result = {}
            for field_name, field_info in model_class.model_fields.items():
                # Check if field has a real default (not PydanticUndefined)
                if (
                    field_info.default is not PydanticUndefined
                    and field_info.default is not None
                ):
                    default_val = field_info.default
                    # Convert Path to string for YAML
                    if isinstance(default_val, Path):
                        default_val = str(default_val)
                    result[field_name] = default_val
                # Recurse for any nested Pydantic BaseModel
                elif isinstance(field_info.annotation, type) and issubclass(
                    field_info.annotation, BaseModel
                ):
                    result[field_name] = schema_to_dict(field_info.annotation)
                # Placeholder for required primitive fields
                else:
                    result[field_name] = 0
            return result

        # Generate structure from FileSettings schema
        default_structure = schema_to_dict(FileSettings)

        # Merge existing data into default structure
        merged = deep_merge(default_structure, existing_data)

        return (
            "# ZORSBOT Configuration\n"
            "# Edit values below for your Discord server\n\n"
            + yaml.dump(merged, default_flow_style=False, sort_keys=False)
        )


class _LazySettings:
    """Lazy-loading settings. Loads on first attribute access."""

    _instance: AppSettings | None = None

    def __getattr__(self, name: str):
        if self._instance is None:
            self._instance = AppSettings.load()
        return getattr(self._instance, name)


# Global settings - loads on first access
settings = _LazySettings()
