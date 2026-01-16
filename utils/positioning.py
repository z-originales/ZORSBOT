"""Utilities for positioning Discord objects (roles, channels)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, Protocol, runtime_checkable

import discord
from loguru import logger as log

if TYPE_CHECKING:
    from utils.settings import Placement

# Type alias for Discord positionable objects
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
    """Protocol for Discord objects with a readable position."""

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
    Places an item relative to an anchor in the Discord hierarchy.

    Note on Discord positions:
    - Higher position = larger number (e.g., admin at position 50)
    - Lower position = smaller number (e.g., @everyone at position 0)
    - “before” = above the anchor (position + 1)
    - “after” = below the anchor (position - 1)

    Args:
    item: The object to be positioned (Role, TextChannel, VoiceChannel, etc.)
    anchor: The reference object for placement
        where: “before” (above) or “after” (below) the anchor

    Returns:
    True if placement was successful, False otherwise
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
    Places an item according to a Placement configuration.

    Args:
        item: The object to be positioned (Role, TextChannel, etc.)
        guild: The Discord server
        placement: Configuration with anchor_id, anchor_type, and where

    Returns:
        True if the placement was successful, False otherwise
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
