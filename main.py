import traceback
import sys


import discord
from discord import Guild
from discord.ext import commands
from typing_extensions import override

from utils import logger
from loguru import logger as log
from asyncio import run
from utils.settings import settings, ConfigurationError
from model.database import Database


class ZORS(commands.Bot):
    database: Database

    def __init__(self, *args, **kwargs):
        log.debug("ZORS bot is starting up...")
        super().__init__(*args, **kwargs)
        self.database = Database(str(settings.env.postgres_url))
        log.info("Successfully connected to the database")
        log.trace("ZORS bot has been initialized.")
        log.info("Loading cogs...")

    @classmethod
    async def create_bot(cls) -> "ZORS":
        """
        Creates an instance of the bot.
        Returns: ZORS - Instance of the bot.
        """
        zorsintents = discord.Intents.none()
        zorsintents.members = True
        zorsintents.guilds = True
        zorsintents.guild_messages = True
        zorsintents.bans = True
        zorsintents.emojis_and_stickers = True
        zorsintents.webhooks = True
        zorsintents.messages = True
        zorsintents.message_content = True
        zorsintents.reactions = True
        zorsintents.auto_moderation_configuration = True
        zorsintents.auto_moderation_execution = True
        zorsintents.voice_states = True

        bot = ZORS(
            description="ZORS !",
            activity=discord.Activity(type=discord.ActivityType.custom, name="ZORS !"),
            intents=zorsintents,
            help_command=None,
        )
        await bot.database.create_db_and_tables()
        bot._load_cogs()
        return bot

    @property
    def main_guild(self) -> Guild:
        guild = self.get_guild(settings.config.main_guild)
        if guild is None:
            log.error("Main guild not found.")
            raise ValueError("Main guild not found.")
        return guild

    @override
    async def start(self, *args, **kwargs) -> None:
        """
        Starts the bot with the token from the settings.
        Returns:

        """
        await super().start(settings.env.discord_token, *args, **kwargs)

    def _load_cogs(self) -> None:
        """
        Loads all cogs in the cogs directory recursively.
        python files starting with an underscore aren't started. This is default pycord behavior.

        Returns:

        """
        status = self.load_extensions("cogs", recursive=True, store=True)
        if status is None or isinstance(status, list):
            log.debug("No cogs loaded.")
            return
        for extension, result in status.items():
            match result:
                case True:
                    log.debug(f"Loaded cog: {extension}")
                case discord.ExtensionAlreadyLoaded():
                    log.debug(f"Cog already loaded: {extension} - {result}")
                case discord.ExtensionNotFound():
                    log.error(f"Failed to load cog: {extension} - {result}")
                case discord.NoEntryPointError():
                    log.error(f"Cog has no setup function: {extension} - {result}")
                case discord.ExtensionFailed():
                    log.error(f"Cog failed to load: {extension} - {result}")
                case _:
                    log.error(f"Unknown error: {extension} - {result}")
                    print(traceback.format_exc())


async def main():
    """Main entry point for the bot."""
    # Setup basic logger BEFORE loading settings
    # This ensures ConfigurationError is logged properly
    logger.setup_basic_logger()

    try:
        # Now setup full logger with settings (may raise ConfigurationError)
        logger.setup_logger()

        # Create and start bot
        zors_bot = await ZORS.create_bot()
        await zors_bot.start()
    except ConfigurationError as e:
        # Configuration error - show clean message without traceback
        log.error(str(e))
        sys.exit(1)
    except Exception as e:
        # Unexpected error - show full traceback
        log.critical(
            f"Unexpected error occurred, that forced the bot to shut down: {e}"
        )
        log.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    run(main())
