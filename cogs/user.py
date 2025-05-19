from main import ZORS
from typing import override
from loguru import logger as log
from model.managers import MemberManager
from utils.zors_cog import ZorsCog


class Member(ZorsCog):
    def __init__(self, bot: ZORS):
        self.bot = bot

    @override
    async def checkup(self):
        """
        Checks for new users in the guild and adds them to the database.
        Returns:
        """

        # Prepare the data for the manager (without passing Discord objects)
        members = [member for member in self.bot.main_guild.members if not member.bot]
        members_ids = [member.id for member in members]
        members_names = [member.name for member in members]

        async with self.bot.database.get_session() as session:
            added_indices = await MemberManager.sync_users(
                session, members_ids, members_names
            )

        # Retrieve the names of the added users
        added_users = [members_names[idx] for idx in added_indices]

        log.info(f"Added {len(added_users)} new users to the database.")
        log.debug(f"New users: {added_users}")


def setup(bot: ZORS):
    bot.add_cog(Member(bot))
