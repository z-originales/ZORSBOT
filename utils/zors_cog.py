from __future__ import annotations

import discord
from discord.ext import commands
from loguru import logger as log


class ZorsCog(commands.Cog):
    def __init__(self) -> None:
        super().__init__()

    def require_guild(self, ctx: discord.ApplicationContext) -> discord.Guild:
        """Return ctx.guild or raise a user-facing error."""
        if ctx.guild is None:
            raise commands.NoPrivateMessage(
                "Cette commande doit être utilisée dans un serveur."
            )
        return ctx.guild

    def require_member(self, ctx: discord.ApplicationContext) -> discord.Member:
        """Return ctx.author as Member or raise a user-facing error."""
        author = ctx.author
        if not isinstance(author, discord.Member):
            raise commands.CheckFailure(
                "Cette commande doit être utilisée par un membre."
            )
        return author

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event that is called when the bot is ready.
        Returns:
        """
        log.info(f"running checkup for {self.__class__.__name__}")
        await self.checkup()
        log.debug(f"checkup done for {self.__class__.__name__}")

    async def checkup(self):
        """
        Checkup function that is called when the bot is ready.
        It should be overridden in the cog to execute a checkup logic at the bot startup.
        Returns:
        """
