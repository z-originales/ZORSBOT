import discord
from discord.ext import commands
from utils import logger, utilities
from loguru import logger as log
from prisma import Prisma

class ZORS(commands.Bot):

    def __init__(self, env_vars=None, *args, **kwargs):
        log.debug("ZORS bot is starting up...")
        super().__init__(*args, **kwargs)
        self.envs = env_vars
        self.database = Prisma()
        self.database.connect()
        log.info("Succesfully connected to the database")
        log.trace("ZORS bot has been initialized.")
        log.info("ZORS bot is ready to go.")
        log.debug("Loading cogs...")
        self._load_cogs()

    async def check_for_new_users(self)->bool:
        """
        Checks for new users in the guild and adds them to the database if they are not already in it.
        :return: bool - True if new users were added, False if no new users were added.
        """
        new_users = False
        for guild in self.guilds:
            for member in guild.members:
                if not self.database.client.get_user(member.id):
                    new_users = True
                    await self.database.client.create_user(member.id, member.name)
        return new_users

    async def on_ready(self):
        """
        Event that is called when the bot is ready.
        Returns:

        """
        log.debug("ZORS bot is up and ready.")
        log.trace(f"Logged in as {self.user} ({self.user.id})")
        log.debug("Checking for new users...")
        if await self.check_for_new_users():
            log.info("Added new users to the database.")

    def _load_cogs(self) -> None:
        """
        Loads all cogs in the cogs directory recursively.
        python files starting with an underscore aren't started. This is default pycord behavior.

        Returns:

        """
        status = self.load_extensions("cogs", recursive=True, store=True)
        for extension in status:
            match status[extension]:
                case True:
                    log.debug(f"Loaded cog: {extension}")
                case discord.ExtensionAlreadyLoaded:
                    log.debug(f"Cog already loaded: {extension} - {status[extension]}")
                case discord.ExtensionNotFound:
                    log.error(f"Failed to load cog: {extension} - {status[extension]}")
                case discord.NoEntryPointError:
                    log.error(f"Cog has no setup function: {extension} - {status[extension]}")
                case discord.ExtensionFailed:
                    log.error(f"Cog failed to load: {extension} - {status[extension]}")
                case _:
                    log.error(f"Unknown error: {extension} - {status[extension]}")

@log.catch(level="CRITICAL", message="Unexpected error occurred, that forced the bot to shut down.")
def main() -> None:

    try:
        env_vars = utilities.get_required_env_vars()
        logger.setup_logger('logs' if "LOGS_PATH" not in env_vars else env_vars["LOGS_PATH"], "DEBUG")
    except EnvironmentError as e:
        log.critical(f"Failed to start the bot: {e}")
        exit(1)

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

    zors = ZORS(
        description="ZORS !",
        activity=discord.Game(name="/ping for now"),
        intents=zorsintents,
        help_command=None
    )
    zors.run(env_vars["DISCORD_TOKEN"])

if __name__ == "__main__":
    main()
