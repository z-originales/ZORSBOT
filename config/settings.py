from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource, YamlConfigSettingsSource, EnvSettingsSource
from pydantic import PostgresDsn, computed_field
from yaml import safe_load
from pathlib import Path

config_path = Path(__file__).parent / "config.yaml"
dotenv_path = Path(__file__).parent.parent / ".env"

class Settings(BaseSettings):

    #region .env
    discord_token: str
    postgres_url: PostgresDsn
    postgres_password: str
    #endregion

    #region config.yaml
    habitue_role_name: str
    log_level: str
    logs_path: Path
    #endregion

    model_config = SettingsConfigDict(yaml_file=config_path, env_file=dotenv_path)

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            YamlConfigSettingsSource(settings_cls), dotenv_settings, env_settings
        )

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


settings:Settings = Settings() #type: ignore[attr-defined]