from discord.ext import commands
import discord

from loguru import logger as log
from main import ZORS

class Listeners(commands.Cog):
    def __init__(self, bot:ZORS):
        self.bot = bot

    @discord.Cog.listener()
    async def on_application_command(self, ctx:commands.Context):
        log.trace(
            f"Received command: {ctx.command} was invoked by {ctx.author}"
        )

    @discord.Cog.listener()
    async def on_application_command_error(self, ctx:discord.ApplicationContext, error: commands.CommandError|commands.MissingRole):
        message_beginning = f"An error occurred while executing the command {ctx.command}."
        match type(error):
            case commands.MissingRole:
                missing_rolename = error.missing_role
                roleid = str(discord.utils.get(ctx.guild.roles, name=missing_rolename).id)
                log.error(
                    f"{message_beginning} - MissingRole: {missing_rolename} for {ctx.author}, that shouldn't happen "
                    f"check the integration settings and make sure this command is only visible to the right role."
                )
                await ctx.respond(
                    f"You don't have the required role <@&{roleid}> to execute this command and "
                    f"shouldn't be able to see it. Please contact an admin so he can manage the command access."
                    , allowed_mentions=None
                )
            case _:
                log.error(
                    f"{message_beginning} - Error: {error}"
                )
                await ctx.respond(
                    "An error occurred while executing the command. Please contact an admin."
                )
                raise error

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        log.trace(
            f"Member {member} joined the server."
        )
        await self.bot.database.client.create_user(member.id, member.name)

    @discord.Cog.listener()
    async def on_member_remove(self,member:discord.Member):
        log.trace(
            f"Member {member} left the server."
        )
        await self.bot.database.client.delete_user(member.id)


def setup(bot):
    bot.add_cog(Listeners(bot))
