from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ping", description="Check if the bot is alive.")
    async def ping(self, ctx):
        await ctx.respond(f"Pong! thanks for checking on me {ctx.author.mention} !")


def setup(bot):
    bot.add_cog(Fun(bot))
