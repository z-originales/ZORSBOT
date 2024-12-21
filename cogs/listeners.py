from discord.ext.commands import Context
from discord.ext import commands
import discord


class Listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_application_command(self, ctx):
        self.bot.logger.trace(
            f"Received command: {ctx.command} was invoked by {ctx.author}"
        )

    @discord.Cog.listener()
    async def on_application_command_error(self, ctx, error):
        message_beginning = f"An error occurred while executing the command {ctx.command}."
        match type(error):
            case commands.MissingRole:
                missing_rolename = error.missing_role
                roleid = str(discord.utils.get(ctx.guild.roles, name=missing_rolename).id)
                self.bot.logger.error(
                    f"{message_beginning} - MissingRole: {missing_rolename} for {ctx.author}, that shouldn't happen "
                    f"check the integration settings and make sure this command is only visible to the right role."
                )
                await ctx.respond(
                    f"You don't have the required role <@&{roleid}> to execute this command and "
                    f"shouldn't be able to see it. Please contact an admin so he can manage the command access."
                    , allowed_mentions=None
                )
            case _:
                self.bot.logger.error(
                    f"{message_beginning} - Error: {error}"
                )
                await ctx.respond(
                    "An error occurred while executing the command. Please contact an admin."
                )
                raise error


def setup(bot):
    bot.add_cog(Listeners(bot))
