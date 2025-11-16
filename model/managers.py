from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from model.schemas import Habitue, User, GameCategory, Party, Streamer
import discord
from loguru import logger as log


class MemberManager:
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

    # region utility functions
    @classmethod
    async def sync_users(
        cls, session: AsyncSession, members_ids: list[int], members_names: list[str]
    ) -> list[int]:
        """
        Synchronise les utilisateurs dans la base de données.
        Ajoute uniquement les membres qui n'existent pas encore.

        Args:
            session: La session de base de données
            members_ids: Liste des IDs des membres à synchroniser
            members_names: Liste des noms des membres à synchroniser (même ordre que members_ids)

        Returns:
            Une liste des indices des utilisateurs qui ont été ajoutés
        """
        if not members_ids or not members_names:
            log.error("No members to sync.")
            return []

        added_users_indices = []
        results = await session.exec(select(User))
        users = results.all()
        existing_user_ids = [user.id for user in users]

        for idx, (member_id, member_name) in enumerate(zip(members_ids, members_names)):
            if member_id not in existing_user_ids:
                new_user = User(id=member_id, name=member_name)
                session.add(new_user)
                added_users_indices.append(idx)

        await session.commit()
        return added_users_indices

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

    @classmethod
    async def sync_habitues(
        cls,
        session: AsyncSession,
        members_ids: list[int],
        members_with_habitue_role: list[bool],
    ) -> list[int]:
        """
        Synchronise les habitués dans la base de données.
        Ajoute uniquement les membres qui n'existent pas encore comme habitués.

        Args:
            session: La session de base de données
            members_ids: Liste des IDs des membres à vérifier
            members_with_habitue_role: Liste booléenne indiquant si le membre a le rôle habitué (même ordre que members_ids)

        Returns:
            Une liste des indices des habitués qui ont été ajoutés
        """
        added_habitues_indices = []
        results = await session.exec(select(Habitue))
        habitues = results.all()
        existing_habitue_ids = [habitue.id for habitue in habitues]

        for idx, (member_id, has_role) in enumerate(
            zip(members_ids, members_with_habitue_role)
        ):
            if has_role and member_id not in existing_habitue_ids:
                new_habitue = Habitue(id=member_id, color="#000000")
                session.add(new_habitue)
                added_habitues_indices.append(idx)

        await session.commit()
        return added_habitues_indices

    # endregion


class StreamerManager:
    """
    Gestionnaire pour les entités Streamer dans la base de données.
    """

    @classmethod
    async def add(
        cls, session: AsyncSession, streamer_id: int, channel_tag: str | None = None
    ):
        """
        Ajoute un streamer à la base de données.

        Args:
            session: La session de base de données
            streamer_id: L'ID Discord du streamer
            channel_tag: Tag optionnel pour le canal du streamer

        Returns:
            Le nouvel objet Streamer créé
        """
        new_streamer = Streamer(id=streamer_id, channel_tag=channel_tag)
        session.add(new_streamer)
        await session.commit()
        log.debug(f"DATABASE: Added streamer {streamer_id}")
        return new_streamer

    @classmethod
    async def sync_streamers(
        cls,
        session: AsyncSession,
        members_ids: list[int],
        members_with_streamer_role: list[bool],
    ) -> list[int]:
        """
        Synchronise les streamers dans la base de données.
        Ajoute uniquement les membres qui n'existent pas encore comme streamers.

        Args:
            session: La session de base de données
            members_ids: Liste des IDs des membres à vérifier
            members_with_streamer_role: Liste booléenne indiquant si le membre a le rôle streamer (même ordre que members_ids)

        Returns:
            Une liste des indices des streamers qui ont été ajoutés
        """
        added_streamers_indices = []
        results = await session.exec(select(Streamer))
        streamers = results.all()
        existing_streamer_ids = [streamer.id for streamer in streamers]

        for idx, (member_id, has_role) in enumerate(
            zip(members_ids, members_with_streamer_role)
        ):
            if has_role and member_id not in existing_streamer_ids:
                new_streamer = Streamer(id=member_id, channel_tag=None)
                session.add(new_streamer)
                added_streamers_indices.append(idx)

        await session.commit()
        return added_streamers_indices


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
        role_id: int,
    ):
        new_game_category = GameCategory(
            id=category_id,
            name=game_name,
            forum_id=forum_id,
            text_id=text_id,
            voice_id=voice_id,
            role_id=role_id,
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
            owner: User | None = await MemberManager.get_by_id(session, party.owner_id)
            if owner is not None:
                log.debug(f"DATABASE: Deleted party {party.name} owned by {owner.name}")
            else:
                log.debug(
                    f"DATABASE: Deleted party {party.name} owned by {party.owner_id}"
                )
            return True
        return False

    # endregion
