"""Utilitaires pour le positionnement des objets Discord (rôles, channels)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

import discord
from loguru import logger as log

if TYPE_CHECKING:
    from utils.settings import Placement

# Type alias pour les objets Discord positionnables
PositionableType = (
    discord.Role
    | discord.TextChannel
    | discord.VoiceChannel
    | discord.CategoryChannel
    | discord.ForumChannel
    | discord.StageChannel
)


@runtime_checkable
class HasPosition(Protocol):
    """Protocol pour les objets Discord avec une position lisible."""

    @property
    def position(self) -> int: ...
    @property
    def name(self) -> str: ...


async def place_relative(
    item: PositionableType,
    anchor: HasPosition,
    where: Literal["before", "after"] = "after",
) -> bool:
    """
    Place un item relativement à un ancre dans la hiérarchie Discord.

    Note sur les positions Discord:
    - Position plus haute = nombre plus grand (ex: admin à position 50)
    - Position plus basse = nombre plus petit (ex: @everyone à position 0)
    - "before" = au-dessus de l'ancre (position + 1)
    - "after" = en-dessous de l'ancre (position - 1)

    Args:
        item: L'objet à positionner (Role, TextChannel, VoiceChannel, etc.)
        anchor: L'objet de référence pour le placement
        where: "before" (au-dessus) ou "after" (en-dessous) de l'ancre

    Returns:
        True si le placement a réussi, False sinon
    """
    target_pos = anchor.position + 1 if where == "before" else anchor.position - 1

    try:
        await item.edit(position=target_pos)
        log.debug(
            f"Positionné '{item.name}' {where} '{anchor.name}' (position {target_pos})"
        )
        return True
    except discord.HTTPException as e:
        log.warning(f"Impossible de positionner '{item.name}': {e}")
        return False


async def place_with_config(
    item: PositionableType,
    guild: discord.Guild,
    placement: Placement,
) -> bool:
    """
    Place un item selon une configuration Placement.

    Args:
        item: L'objet à positionner (Role, TextChannel, etc.)
        guild: Le serveur Discord
        placement: Configuration avec anchor_id, anchor_type et where

    Returns:
        True si le placement a réussi, False sinon
    """
    anchor: HasPosition | None = None

    if placement.anchor_type == "role":
        anchor = guild.get_role(placement.anchor_id)
    else:
        anchor = guild.get_channel(placement.anchor_id)

    if anchor is None or not isinstance(anchor, HasPosition):
        log.warning(
            f"{placement.anchor_type.capitalize()} d'ancrage (ID: {placement.anchor_id}) "
            f"introuvable pour le placement de '{item.name}'"
        )
        return False

    return await place_relative(item, anchor, placement.where)
