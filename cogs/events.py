from discord import ApplicationContext, DiscordException
from discord.ext import commands
import discord

from loguru import logger as log
from model.managers import UserManager
from main import ZORS


class Events(commands.Cog):
    def __init__(self, bot: ZORS):
        self.bot = bot
        self.bot.before_invoke(self._log_every_command)

    async def _log_every_command(self, ctx: ApplicationContext):
        """
        Logs every command called by a user.
        This is used instead of the default on_application_command since it runs in parallel with the command not before it.
        Args:
            ctx: The context of the command.

        Returns:

        """
        log.trace(f"Command {ctx.command} called by {ctx.author}.")

    @discord.Cog.listener()
    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        error, # not typed because it can be any exception
    ):
        message_beginning = (
            f"An error occurred while executing the command {ctx.command}."
        )
        match type(error):
            case commands.MissingRole:
                # Au lieu de redéfinir error, utilisez-le directement
                missing_role = error.missing_role
                role = discord.utils.get(ctx.guild.roles, name=missing_role)
                # Vérifiez que le rôle existe avant d'accéder à son ID
                roleid = str(role.id) if role else "rôle inconnu"
                log.error(
                    f"{message_beginning} - MissingRole: {missing_role} for {ctx.author}, that shouldn't happen "
                    f"check the integration settings and make sure this command is only visible to the right role."
                )
                await ctx.respond(
                    f"You don't have the required role <@&{roleid}> to execute this command and "
                    f"shouldn't be able to see it. Please contact an admin so he can manage the command access.",
                    allowed_mentions=discord.AllowedMentions.none()
                )
            case commands.MissingPermissions:
                # Utilisez directement error sans le redéfinir
                missing_permissions = error.missing_permissions
                log.error(
                    f"{message_beginning} - MissingPermissions: {missing_permissions} for {ctx.author}"
                )
                await ctx.respond(
                    "You don't have the required permissions to execute this command. Please contact an admin."
                )
            case _:
                log.error(f"{message_beginning} - Error: {error}")
                await ctx.respond(
                    "An error occurred while executing the command. Please contact an admin."
                )
                raise error

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        log.debug(f"Member {member} joined the server.")
        if member.bot:
            log.debug(f"Member {member} is a bot, skipping.")
            return
        async with self.bot.database.get_session() as session:
            await UserManager.add(session, member)

    @discord.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        log.trace(f"Member {member} left the server.")
        if member.bot:
            log.debug(f"Member {member} is a bot, skipping.")
            return
        async with self.bot.database.get_session() as session:
            await UserManager.delete(session, member)


def setup(bot: ZORS):
    bot.add_cog(Events(bot))
