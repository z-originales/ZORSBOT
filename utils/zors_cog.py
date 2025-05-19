from collections.abc import Coroutine, Callable
from typing import Any
from inspect import isawaitable

from discord.ext import commands
from loguru import logger as log


class ZorsCog(commands.Cog):
    def __init__(self) -> None:
        super().__init__()

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