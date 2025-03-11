from asyncpg import UniqueViolationError
from discord import Member
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from model.schemas import Habitue, User
import discord
from loguru import logger as log


class UserManager:

    #region CRUD
    @classmethod
    async def add(cls,session: AsyncSession, member: discord.Member):
        new_user = User(id=member.id, name=member.display_name)
        session.add(new_user)
        await session.commit()
        log.debug(f"DATABASE: Added user {member.display_name}")

    @classmethod
    async def get_user_from_database(cls, session, member):
        results = await session.exec(
            select(User).where(User.id == member.id)
        )
        user :User= results.first()
        if user is None:
            log.error(f"{member.display_name} isn't found in the User database, database seems out of sync")
            return None
        return user

    @classmethod
    async def update_user(cls,session: AsyncSession, member: discord.Member):
        user = await cls.get_user_from_database(session, member)
        user.name = member.display_name
        await session.commit()
        log.debug(f"DATABSE: Updated {member.display_name}")

    @classmethod
    async def delete(cls,session: AsyncSession,member: discord.Member):
        user = await cls.get_user_from_database(session, member)
        await session.delete(user)
        await session.flush()
        await session.commit()
        log.debug(f"DATBASE: Deleted user {member.display_name}")

    #endregion

    #region utility functions


    #endregion


class HabitueManager:

    #region CRUD
    @classmethod
    async def add(cls, session: AsyncSession, member: discord.Member, color: str|None = None):
        color = color if color is not None else "#000000"
        new_habitue = Habitue(id=member.id, color=color)
        session.add(new_habitue)
        await session.commit()
        log.debug(f"DATBASE: Added habitue {member.display_name}")

    @classmethod
    async def get_habitue_from_database(cls, session: AsyncSession, member: discord.Member) -> Habitue|None:
        results = await session.exec(
            select(Habitue).where(Habitue.id == member.id)
        )
        habitue :Habitue= results.first()
        if habitue is None:
            log.error(f"{member.display_name} isn't found in the Habitue database, are you sure he is one?")
            return None
        return habitue

    @classmethod
    async def update_color(cls, session: AsyncSession, member: discord.Member, color: str):
        habitue :Habitue | None= await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return
        habitue.color = color
        await session.commit()
        log.debug(f"DATBASE: Updated habitue {member.display_name}")

    @classmethod
    async def delete(cls,session: AsyncSession,member: discord.Member):
        habitue = await cls.get_habitue_from_database(session, member)
        await session.delete(habitue)
        await session.flush()
        await session.commit()
        log.debug(f"DATABASE: Deleted habitue {member.display_name}")
    #endregion

    #region utility functions
    @classmethod
    async def get_color(cls, session: AsyncSession, member: discord.Member) -> str|None:
        habitue :Habitue | None= await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return None
        return habitue.color

    @classmethod
    async def get_color_name(cls, session: AsyncSession, member: discord.Member) -> str|None:
        habitue :Habitue | None= await cls.get_habitue_from_database(session, member)
        if habitue is None:
            return None
        return await habitue.color_name #needs to be awaited because it's a coroutine
    #endregion



