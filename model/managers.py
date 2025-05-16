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
        return new_user

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int) -> User | None:
        results = await session.exec(select(User).where(User.id == id))
        user = results.first()
        if user is None:
            log.error(f"User with ID {id} not found in the database")
        return user

    @classmethod
    async def get_by_member(
        cls, session: AsyncSession, member: discord.Member
    ) -> User | None:
        return await cls.get_by_id(session, member.id)

    @classmethod
    async def update(cls, session: AsyncSession, member: discord.Member):
        user = await cls.get_by_id(session, member.id)
        if user is None:
            return None
        user.name = member.display_name
        await session.commit()
        log.debug(f"DATABASE: Updated user {member.display_name}")
        return user

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        user = await cls.get_by_id(session, id)
        if user is not None:
            await session.delete(user)
            await session.commit()
            log.debug(f"DATABASE: Deleted user {user.name} and all related entries")
            return True
        return False

    @classmethod
    async def delete_by_member(cls, session: AsyncSession, member: discord.Member):
        return await cls.delete(session, member.id)

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
        log.debug(f"DATABASE: Added habitue {member.display_name}")
        return new_habitue

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int) -> Habitue | None:
        results = await session.exec(select(Habitue).where(Habitue.id == id))
        habitue = results.first()
        if habitue is None:
            log.error(f"Habitue with ID {id} not found in the database")
        return habitue

    @classmethod
    async def get_by_member(
        cls, session: AsyncSession, member: discord.Member
    ) -> Habitue | None:
        return await cls.get_by_id(session, member.id)

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **kwargs):
        habitue = await cls.get_by_id(session, id)
        if habitue is None:
            return None

        for key, value in kwargs.items():
            if hasattr(habitue, key):
                setattr(habitue, key, value)

        await session.commit()
        log.debug(f"DATABASE: Updated habitue {habitue.id}")
        return habitue

    @classmethod
    async def update_color(
        cls, session: AsyncSession, member: discord.Member, color: str
    ):
        return await cls.update(session, member.id, color=color)

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        habitue = await cls.get_by_id(session, id)
        if habitue is not None:
            await session.delete(habitue)
            await session.commit()
            log.debug(f"DATABASE: Deleted habitue {id}")
            return True
        return False

    @classmethod
    async def delete_by_member(cls, session: AsyncSession, member: discord.Member):
        return await cls.delete(session, member.id)

    # endregion

    # region utility functions
    @classmethod
    async def get_color(
        cls, session: AsyncSession, member: discord.Member
    ) -> str | None:
        habitue = await cls.get_by_member(session, member)
        if habitue is None:
            return None
        return habitue.color

    @classmethod
    async def get_color_name(
        cls, session: AsyncSession, member: discord.Member
    ) -> str | None:
        habitue = await cls.get_by_member(session, member)
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
        return new_game_category

    @classmethod
    async def get_by_id(cls, session: AsyncSession, id: int) -> GameCategory | None:
        results = await session.exec(select(GameCategory).where(GameCategory.id == id))
        game_category = results.first()
        if game_category is None:
            log.error(f"GameCategory with ID {id} not found in the database")
        return game_category

    @classmethod
    async def get_by_name(cls, session: AsyncSession, name: str) -> GameCategory | None:
        results = await session.exec(
            select(GameCategory).where(GameCategory.name == name)
        )
        game_category = results.first()
        if game_category is None:
            log.error(f"GameCategory with name {name} not found in the database")
        return game_category

    @classmethod
    async def get_all(cls, session) -> list[GameCategory]:
        results = await session.exec(select(GameCategory))
        return results.all()

    @classmethod
    async def update(cls, session: AsyncSession, id: int, **kwargs):
        game_category = await cls.get_by_id(session, id)
        if game_category is None:
            return None

        for key, value in kwargs.items():
            if hasattr(game_category, key):
                setattr(game_category, key, value)

        await session.commit()
        log.debug(f"DATABASE: Updated game category {game_category.name}")
        return game_category

    @classmethod
    async def update_by_name(cls, session: AsyncSession, name: str, **kwargs):
        game_category = await cls.get_by_name(session, name)
        if game_category is None:
            return None
        return await cls.update(session, game_category.id, **kwargs)

    @classmethod
    async def delete(cls, session: AsyncSession, id: int):
        game_category = await cls.get_by_id(session, id)
        if game_category is not None:
            await session.delete(game_category)
            await session.commit()
            log.debug(f"DATABASE: Deleted game category {game_category.name}")
            return True
        return False

    @classmethod
    async def delete_by_name(cls, session: AsyncSession, name: str):
        game_category = await cls.get_by_name(session, name)
        if game_category is None:
            return False
        return await cls.delete(session, game_category.id)

    # endregion

    # region utility functions
    @classmethod
    async def get_channels(
        cls, session: AsyncSession, name: str
    ) -> tuple[int, int, int] | None:
        game_category = await cls.get_by_name(session, name)
        if game_category is None:
            return None
        return game_category.forum_id, game_category.text_id, game_category.voice_id

    @classmethod
    async def get_parties(cls, session: AsyncSession, name: str) -> list[Party] | None:
        game_category = await cls.get_by_name(session, name)
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
        channel_id: int,
    ):
        new_party = Party(
            channel_id=channel_id,
            game_category_id=game_category.id,
            name=name,
            owner_id=owner.id,
        )
        session.add(new_party)
        await session.commit()
        log.debug(f"DATABASE: Added party {name} owned by {owner.display_name}")
        return new_party

    @classmethod
    async def get_by_channel_id(
        cls, session: AsyncSession, channel_id: int
    ) -> Party | None:
        results = await session.exec(
            select(Party).where(Party.channel_id == channel_id)
        )
        party = results.first()
        if party is None:
            log.warning(f"No party found with channel_id {channel_id}")
        return party

    @classmethod
    async def get_by_owner(cls, session: AsyncSession, owner_id: int) -> list[Party]:
        query = select(Party).where(Party.owner_id == owner_id)
        results = await session.exec(query)
        return list(results.all())

    @classmethod
    async def get_by_owner_and_game(
        cls, session: AsyncSession, owner_id: int, game_category_id: int
    ) -> list[Party]:
        query = select(Party).where(
            Party.owner_id == owner_id, Party.game_category_id == game_category_id
        )
        results = await session.exec(query)
        return list(results.all())

    @classmethod
    async def update(cls, session: AsyncSession, channel_id: int, **kwargs):
        party = await cls.get_by_channel_id(session, channel_id)
        if party is None:
            return None

        for key, value in kwargs.items():
            if hasattr(party, key):
                setattr(party, key, value)

        await session.commit()
        log.debug(f"DATABASE: Updated party {party.name}")
        return party

    @classmethod
    async def delete(cls, session: AsyncSession, channel_id: int):
        party = await cls.get_by_channel_id(session, channel_id)
        if party is not None:
            await session.delete(party)
            await session.commit()
            owner: User | None = await UserManager.get_by_id(session, party.owner_id)
            if owner is not None:
                owner = await UserManager.get_by_id(session, party.owner_id)
                log.debug(f"DATABASE: Deleted party {party.name} owned by {owner.name}")
            else:
                log.debug(
                    f"DATABASE: Deleted party {party.name} owned by {party.owner_id}"
                )
            return True
        return False

    # endregion
