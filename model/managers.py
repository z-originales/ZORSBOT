from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from model.schemas import Habitue, User, GameCategory, Party
import discord
from loguru import logger as log


class UserManager:
    # region CRUD
    @classmethod
    async def add(cls, session: AsyncSession, member: discord.Member):
        new_user = User(id=member.id, name=member.display_name)
        session.add(new_user)
        await session.commit()
        log.debug(f"DATABASE: Added user {member.display_name}")

    @classmethod
    async def get_user_from_database(
        cls, session: AsyncSession, member: discord.Member
    ):
        results = await session.exec(select(User).where(User.id == member.id))
        user: User | None = results.first()
        if user is None:
            log.error(
                f"{member.display_name} isn't found in the User database, database seems out of sync"
            )
            return None
        return user

    @classmethod
    async def update_user(cls, session: AsyncSession, member: discord.Member):
        user = await cls.get_user_from_database(session, member)
        user.name = member.display_name
        await session.commit()
        log.debug(f"DATABSE: Updated {member.display_name}")

    @classmethod
    async def delete(cls, session: AsyncSession, member: discord.Member):
        user = await cls.get_user_from_database(session, member)
        if user is not None:
            await session.delete(user)
            await session.commit()
            log.debug(f"DATABASE: Deleted user {member.display_name} and all related entries")

    # endregion

    # region utility functions

    # endregion


class HabitueManager:
    # region CRUD
    @classmethod
    async def add(
        cls, session: AsyncSession, member: discord.Member, color: str | None = None
    ):
        color = color if color is not None else "#000000"
        new_habitue = Habitue(id=member.id, color=color)
        session.add(new_habitue)
        await session.commit()
        log.debug(f"DATBASE: Added habitue {member.display_name}")

    @classmethod
    async def get_habitue_from_database(
        cls, session: AsyncSession, member: discord.Member
    ) -> Habitue | None:
        results = await session.exec(select(Habitue).where(Habitue.id == member.id))
        habitue: Habitue | None = results.first()
        if habitue is None:
            log.error(
                f"{member.display_name} isn't found in the Habitue database, are you sure he is one?"
            )
            return None
        return habitue

    @classmethod
    async def update_color(
        cls, session: AsyncSession, member: discord.Member, color: str
    ):
        habitue: Habitue | None = await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return
        habitue.color = color
        await session.commit()
        log.debug(f"DATBASE: Updated habitue {member.display_name}")

    @classmethod
    async def delete(cls, session: AsyncSession, member: discord.Member):
        habitue = await cls.get_habitue_from_database(session, member)
        if habitue is not None:
            await session.delete(habitue)
            await session.commit()
            log.debug(f"DATABASE: Deleted habitue {member.display_name}")

    # endregion

    # region utility functions
    @classmethod
    async def get_color(
        cls, session: AsyncSession, member: discord.Member
    ) -> str | None:
        habitue: Habitue | None = await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return None
        return habitue.color

    @classmethod
    async def get_color_name(
        cls, session: AsyncSession, member: discord.Member
    ) -> str | None:
        habitue: Habitue | None = await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return None
        return await habitue.color_name  # needs to be awaited because it's a coroutine

    # endregion


class GameCategoryManager:
    # region CRUD
    @classmethod
    async def add(
        cls,
        session: AsyncSession,
        category_id: int,
        game_name: str,
        forum_id: int,
        text_id: int,
        voice_id: int,
    ):
        new_game_category = GameCategory(
            id=category_id,
            name=game_name,
            forum_id=forum_id,
            text_id=text_id,
            voice_id=voice_id,
        )
        session.add(new_game_category)
        await session.commit()
        log.debug(f"DATABASE: Added game category {game_name}")

    @classmethod
    async def get_all(cls, session):
        results = await session.exec(select(GameCategory))
        game_categories = results.all()
        if len(game_categories) == 0:
            log.error("No game categories found in the database")
            return None
        return game_categories

    @classmethod
    async def get_game_category_from_database(
        cls, session: AsyncSession, name: str
    ) -> GameCategory | None:
        results = await session.exec(
            select(GameCategory).where(GameCategory.name == name)
        )
        game_category: GameCategory | None = results.first()
        if game_category is None:
            log.error(
                f"{name} isn't found in the GameCategory database, are you sure it exists?"
            )
            return None
        return game_category

    @classmethod
    async def update_game_category(
        cls,
        session: AsyncSession,
        name: str,
        forum_id: int,
        text_id: int,
        voice_id: int,
    ):
        game_category: GameCategory | None = await cls.get_game_category_from_database(
            session, name
        )
        if game_category is None:
            return
        game_category.forum_id = forum_id
        game_category.text_id = text_id
        game_category.voice_id = voice_id
        await session.commit()
        log.debug(f"DATABASE: Updated game category {name}")

    @classmethod
    async def delete(cls, session: AsyncSession, name: str):
        game_category = await cls.get_game_category_from_database(session, name)
        if game_category is not None:
            await session.delete(game_category)
            await session.commit()
            log.debug(f"DATABASE: Deleted game category {name}")

    # endregion

    # region utility functions
    @classmethod
    async def get_channels(
        cls, session: AsyncSession, name: str
    ) -> tuple[int, int, int] | None:
        game_category: GameCategory | None = await cls.get_game_category_from_database(
            session, name
        )
        if game_category is None:
            return None
        return game_category.forum_id, game_category.text_id, game_category.voice_id

    @classmethod
    async def get_parties(cls, session: AsyncSession, name: str) -> list[Party] | None:
        game_category: GameCategory | None = await cls.get_game_category_from_database(
            session, name
        )
        if game_category is None:
            return None
        return game_category.parties

    # endregion


class PartyManager:
    # region CRUD
    @classmethod
    async def add(
        cls,
        session: AsyncSession,
        game_category: GameCategory,
        name: str,
        owner: discord.Member,
    ):
        new_party = Party(
            game_category_id=game_category.id, name=name, owner_id=owner.id
        )
        session.add(new_party)
        await session.commit()
        log.debug(f"DATABASE: Added party {name} owned by {owner.display_name}")

    @classmethod
    async def get_party_from_database(
        cls, session: AsyncSession, party_id: int
    ) -> Party | None:
        results = await session.exec(select(Party).where(Party.id == party_id))
        party: Party | None = results.first()
        if party is None:
            log.error(
                f"party with id {int} isn't found in the Party database, are you sure it exists?"
            )
            return None
        return party

