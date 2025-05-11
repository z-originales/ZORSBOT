from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
    PydanticBaseSettingsSource,
    YamlConfigSettingsSource,
)
from pydantic import computed_field
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"
dotenv_path = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # region .env
    discord_token: str
    postgres_password: str
    postgres_user: str
    postgres_db: str
    postgres_host: str
    postgres_port: str
    postgres_scheme: str
    # endregion

    # region config.yaml
    habitue_role_name: str
    log_level: str
    logs_path: Path
    # endregion

    @computed_field
    @property
    def postgres_url(self) -> str:
        """
        Returns the postgres url
        Returns:
            str: postgres url
        """
        return f"{self.postgres_scheme}://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    model_config = SettingsConfigDict(
        yaml_file=config_path, env_file=dotenv_path, extra="ignore"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return YamlConfigSettingsSource(settings_cls), env_settings, dotenv_settings

    def edit_variables(self):
        """
        Edit the variables in the settings
        Returns:

        """
        # TODO add a method to edit the variables
        pass

    def reload_settings(self):
        """
        Reload the settings from the sources.
        Returns:

        """
        self.__init__()


settings: Settings = Settings()  # type: ignore[attr-defined]
