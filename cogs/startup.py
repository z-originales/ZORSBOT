from discord.ext import commands
from sqlmodel import select

from model.managers import HabitueManager
from model.schemas import User, Habitue, Streamer

from loguru import logger as log
import asyncio

from main import ZORS


class Startup(commands.Cog):
    def __init__(self, bot: ZORS):
        self.bot = bot

    async def checkup(self) -> None:
        """
        Performs a full checkup.
        :return: None
        """
        await self.check_for_users()
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self.check_for_habitues())
            # tg.create_task(self.check_for_streamers()) # need to be reimplemented like the check for habitues

    async def check_for_users(self) -> None:
        """
        Checks for new users in the guild and adds them to the database.
        Returns:
        """
        log.debug("Checking for new users...")
        added_users = []
        async with self.bot.database.get_session() as session:
            for member in [
                member for member in self.bot.main_guild.members if not member.bot
            ]:
                results = await session.exec(select(User))
                users = results.all()
                if member.id in [
                    user.id for user in users
                ]:  # user is already in the database
                    continue
                new_user = User(id=member.id, name=member.name)
                session.add(new_user)
                added_users.append(member.name)
            await session.commit()
        log.info(f"Added {len(added_users)} new users to the database.")
        log.debug(f"New users: {added_users}")

    async def check_for_habitues(self) -> None:
        """
        Checks for new habitues in the guild and adds them to the database.
        Returns:
        """
        log.debug("Checking for new habitues...")
        added_habitues = []
        async with self.bot.database.get_session() as session:
            for member in [
                member for member in self.bot.main_guild.members if not member.bot
            ]:
                user_role_list = [role.name for role in member.roles]
                if "Les Habitués" in user_role_list:
                    results = await session.exec(select(Habitue))
                    habitues = results.all()
                    if member.id in [habitue.id for habitue in habitues]:
                        continue
                    await HabitueManager.add(session, member)
                    added_habitues.append(member.name)
            await session.commit()
        log.info(f"Added {len(added_habitues)} new habitues to the database.")
        log.debug(f"New habitues: {added_habitues}")

    async def check_for_streamers(self) -> None:
        """
        Checks for new streamers in the guild and adds them to the database.
        Returns:
        """
        log.debug("Checking for new streamers...")
        added_streamers = []
        async with self.bot.database.get_session() as session:
            for member in [
                member for member in self.bot.main_guild.members if not member.bot
            ]:
                user_role_list = [role.name for role in member.roles]
                if "Streamer" in user_role_list:
                    results = await session.exec(select(Streamer))
                    streamers = results.all()
                    if member.id in [streamer.id for streamer in streamers]:
                        continue
                    new_streamer = Streamer(id=member.id, channel_tag=None)
                    session.add(new_streamer)
                    added_streamers.append(member.name)
            await session.commit()
        log.info(f"Added {len(added_streamers)} new streamers to the database.")
        log.debug(f"New streamers: {added_streamers}")

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Event that is called when the bot is ready.
        Returns:
        """
        self.bot.main_guild = self.bot.guilds[0]
        log.debug("ZORS bot is up and ready.")
        log.trace(f"Logged in as {self.bot.user} ({self.bot.user.id})")
        await self.checkup()


def setup(bot: ZORS):
    bot.add_cog(Startup(bot))
