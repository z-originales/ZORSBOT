from functools import cached_property
from typing import cast

import discord
from discord import Member, Guild, Role
from discord.ext import commands
from typing import override

from utils.settings import settings
from main import ZORS
from model.managers import HabitueManager
from loguru import logger as log

from utils.zors_cog import ZorsCog

# Define default colors at module level for decorator access
default_colors = {
    "blue": discord.Color.blue(),
    "blurple": discord.Color.blurple(),
    "fuchsia": discord.Color.fuchsia(),
    "gold": discord.Color.gold(),
    "green": discord.Color.green(),
    "greyple": discord.Color.greyple(),
    "magenta": discord.Color.magenta(),
    "og_blurple": discord.Color.blurple(),
    "orange": discord.Color.orange(),
    "purple": discord.Color.purple(),
    "red": discord.Color.red(),
    "teal": discord.Color.teal(),
    "yellow": discord.Color.yellow(),
}


class Habitue(ZorsCog):
    category_role = "==COULEURS HABITUÉS=="
    habitue_colorname_template = "couleur {username}"
    _processed_habitue: Member | None = (
        None  # TODO turn it into a set to handle multiple members being processed at the same time
    )

    def __init__(self, bot: ZORS):
        self.bot = bot

    @cached_property
    def role_habitue(self) -> Role:
        role = discord.utils.get(
            self.bot.main_guild.roles, id=settings.config.roles.lesHabitues.id
        )
        if role is None:
            log.error("Role 'Les Habitués' not found in the guild.")
            raise ValueError("Role 'Les Habitués' not found in the guild.")
        return role

    @commands.Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if self._processed_habitue:
            if before.id == self._processed_habitue.id:
                return
        if self.role_habitue not in before.roles and self.role_habitue in after.roles:
            log.info(f"{after.display_name} was given the habitue role")
            await self._add_habitue(after.guild, after)
        elif self.role_habitue in before.roles and self.role_habitue not in after.roles:
            log.info(f"{after.display_name} was removed from the habitue role")
            await self._remove_habitue(after.guild, after)

    @commands.slash_command(
        name="add_habitue", description="Add a habitue to the server."
    )
    @commands.has_permissions(manage_roles=True)
    @discord.option(
        name="member",
        description="The member you want to add.",
        type=discord.Member,
        required=True,
    )
    @discord.option(
        name="color",
        description="The color you want to set as a hex code (#XXYYZZ).",
        type=str,
        required=False,
    )
    async def add_habitue_command(
        self, ctx: discord.ApplicationContext, member: Member, color: str | None = None
    ):
        if self.role_habitue in member.roles:
            log.error(f"{member.display_name} is already an habitue")
            await ctx.respond(f"{member.display_name} is already an habitue")
        else:
            await self._add_habitue(ctx.guild, member, color)
            guild = self.require_guild(ctx)
            await self._add_habitue(guild, member, color)
            await ctx.respond(f"{member.display_name} has been added has an habitue.")

    @commands.slash_command(
        name="remove_habitue", description="Remove a habitue from the server."
    )
    @commands.has_permissions(manage_roles=True)
    @discord.option(
        name="member",
        description="The member you want to remove.",
        type=discord.Member,
        required=True,
    )
    async def remove_habitue_command(
        self, ctx: discord.ApplicationContext, member: Member
    ):
        if self.role_habitue not in member.roles:
            log.error(f"{member.display_name} is not an habitue")
            await ctx.respond(f"{member.display_name} is not an habitue")
        else:
            await self._remove_habitue(ctx.guild, member)
            guild = self.require_guild(ctx)
            await self._remove_habitue(guild, member)
            await ctx.respond(f"{member.display_name} has been removed as an habitue.")

    @commands.slash_command(name="set_custom_color", description="Set your color.")
    @commands.has_role(settings.config.roles.lesHabitues.id)
    @discord.option(
        name="red",
        description="The amount of red you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    @discord.option(
        name="green",
        description="The amount of green you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    @discord.option(
        name="blue",
        description="The amount of blue you want to set.",
        type=int,
        required=True,
        min_value=0,
        max_value=255,
    )
    async def set_custom_color(
        self, ctx: discord.ApplicationContext, red: int, green: int, blue: int
    ):
        try:
            member = self.require_member(ctx)
            color_name = await self._update_user_color(member, red, green, blue)

            await ctx.respond(
                f"Your color has been set to {color_name}.", ephemeral=True
            )
        except ValueError as e:
            log.error(f"Erreur lors de la mise à jour de la couleur : {e}")
            await ctx.respond(
                f"Une erreur s'est produite lors de la mise à jour de votre couleur: {e}",
                ephemeral=True,
            )

    @commands.slash_command(
        name="set_color", description="Set your color from a list of predefined colors."
    )
    @commands.has_role(settings.config.roles.lesHabitues.id)
    @discord.option(
        name="color",
        description="The color you want to set.",
        type=str,
        required=True,
        choices=list(default_colors.keys()),
    )
    async def set_color(self, ctx: discord.ApplicationContext, color: str):
        r, g, b = default_colors[color].to_rgb()
        await self._update_user_color(ctx.user, r, g, b)
        member = self.require_member(ctx)
        await self._update_user_color(member, r, g, b)
        await ctx.respond(f"Your color has been set to {color}.")

    # region utility functions
    async def _update_user_color(
        self, member: Member, red: int, green: int, blue: int
    ) -> str:
        role = discord.utils.get(
            member.guild.roles,
            name=self.habitue_colorname_template.format(username=member.display_name),
        )
        if role is None:
            log.warning(
                f"Role {self.habitue_colorname_template.format(username=member.display_name)} not found in the guild {member.guild.name}"
            )
            if self.role_habitue in member.roles:
                log.warning(
                    f"{member.display_name} seems to be an habitue, creating the color role"
                )
                try:
                    role = await self._create_color_role(
                        member.guild, member.display_name
                    )
                    await member.add_roles(cast(discord.abc.Snowflake, role))
                except ValueError as e:
                    log.error(f"Erreur lors de la création du rôle de couleur : {e}")
                    raise ValueError(
                        f"Impossible de créer le rôle de couleur pour {member.display_name}: {e}"
                    )
                except discord.Forbidden as e:
                    log.error(
                        f"Permissions insuffisantes pour créer le rôle de couleur : {e}"
                    )
                    raise ValueError(
                        f"Permissions insuffisantes pour créer le rôle de couleur pour {member.display_name}"
                    )
                except discord.HTTPException as e:
                    log.error(
                        f"Erreur Discord lors de la création du rôle de couleur : {e}"
                    )
                    raise ValueError(
                        f"Erreur Discord lors de la création du rôle de couleur pour {member.display_name}"
                    )

        if role is None:
            raise ValueError(
                f"Le rôle de couleur pour {member.display_name} est introuvable"
            )

        await role.edit(color=discord.Color.from_rgb(red, green, blue))

        async with self.bot.database.get_session() as session:
            await HabitueManager.update_color(
                session, member, f"#{red:02x}{green:02x}{blue:02x}"
            )
            habitue = await HabitueManager.get_by_member(session, member)
            if habitue is None:
                raise ValueError(
                    f"L'habitué {member.display_name} n'existe pas dans la base de données"
                )

            await session.refresh(habitue)
            color_name = await HabitueManager.get_color_name(session, member)
            if color_name is None:
                raise ValueError(
                    f"Impossible de récupérer le nom de la couleur pour {member.display_name}"
                )
            return color_name

    async def _add_habitue(
        self, guild: Guild, member: Member, color: str | None = None
    ):
        self._processed_habitue = member
        try:
            color_role = await self._create_color_role(guild, member.display_name)
            await member.add_roles(
                cast(discord.abc.Snowflake, self.role_habitue),
                cast(discord.abc.Snowflake, color_role),
            )

            async with self.bot.database.get_session() as session:
                await HabitueManager.add(session, member, color)

            log.info(f"Added habitue {member.display_name} to {guild.name}")

        except ValueError as e:
            log.error(f"Erreur lors de la création du rôle de couleur : {e}")
            # Ajouter uniquement le rôle d'habitué, sans le rôle de couleur
            await member.add_roles(cast(discord.abc.Snowflake, self.role_habitue))
            log.info(
                f"Added habitue {member.display_name} to {guild.name} (without color role)"
            )

        except discord.Forbidden as e:
            log.error(
                f"Permissions insuffisantes pour créer ou ajouter des rôles : {e}"
            )

        except discord.HTTPException as e:
            log.error(f"Erreur Discord lors de l'ajout de l'habitué : {e}")

        finally:
            self._processed_habitue = None

    async def _remove_habitue(self, guild: Guild, member: Member):
        self._processed_habitue = member
        color_role: Role | None = discord.utils.get(
            guild.roles,
            name=self.habitue_colorname_template.format(username=member.display_name),
        )
        if color_role is None:
            log.error(
                f"Role {self.habitue_colorname_template.format(username=member.display_name)} not found in the guild {guild.name}"
            )
            return
        await color_role.delete()
        await member.remove_roles(cast(discord.abc.Snowflake, self.role_habitue))
        async with self.bot.database.get_session() as session:
            await HabitueManager.delete_by_member(session, member)
        log.info(f"Removed habitue {member.display_name} from {guild.name}")
        self._processed_habitue = None

    async def _create_color_role(self, guild: Guild, member_display_name: str) -> Role:
        """
        Crée un rôle de couleur pour un membre habitué.

        Args:
            guild: Le serveur Discord où créer le rôle
            member_display_name: Le nom d'affichage du membre

        Returns:
            Le rôle créé ou existant

        Raises:
            ValueError: Si le rôle catégorie n'existe pas ou si le nom d'affichage est invalide
            discord.Forbidden: Si le bot n'a pas les permissions nécessaires
            discord.HTTPException: Si une erreur Discord se produit lors de la création
        """
        # Vérification que le nom d'affichage est valide
        if not member_display_name or len(member_display_name.strip()) == 0:
            raise ValueError("Le nom d'affichage du membre ne peut pas être vide")

        # Recherche du rôle de catégorie
        category: Role | None = discord.utils.get(guild.roles, name=self.category_role)
        if category is None:
            error_msg = f"Rôle de catégorie '{self.category_role}' introuvable dans le serveur '{guild.name}'"
            log.error(error_msg)
            raise ValueError(error_msg)

        # Définition du nom du rôle de couleur
        color_role_name = self.habitue_colorname_template.format(
            username=member_display_name
        )

        # Vérification si le rôle existe déjà
        existing_role = discord.utils.get(guild.roles, name=color_role_name)
        if existing_role:
            log.debug(f"Rôle de couleur pour '{member_display_name}' déjà existant")
            return existing_role

        try:
            # Création du nouveau rôle avec une couleur par défaut
            log.info(
                f"Création du rôle de couleur '{color_role_name}' pour {member_display_name}"
            )
            role = await guild.create_role(
                name=color_role_name,
                color=discord.Color.from_rgb(0, 0, 0),
                reason=f"Création automatique du rôle de couleur pour l'habitué {member_display_name}",
            )

            # Placement du rôle dans la hiérarchie
            try:
                await role.edit(position=category.position)
            except discord.HTTPException as e:
                log.warning(f"Impossible de positionner le rôle correctement: {e}")
                # On continue car ce n'est pas critique

            log.debug(f"Rôle de couleur créé avec succès pour {member_display_name}")
            return role

        except discord.Forbidden as e:
            error_msg = f"Permissions insuffisantes pour créer le rôle de couleur: {e}"
            log.error(error_msg)
            raise

        except discord.HTTPException as e:
            error_msg = f"Erreur Discord lors de la création du rôle de couleur: {e}"
            log.error(error_msg)
            raise

    # endregion

    @override
    async def checkup(self):
        """
        Checks for new habitues in the guild and adds them to the database.
        Returns:
        """
        # Prepare the data for the manager (without passing Discord objects)
        members = [member for member in self.bot.main_guild.members if not member.bot]
        members_ids = [member.id for member in members]
        members_with_role_habitue = [
            "Les Habitués" in [role.name for role in member.roles] for member in members
        ]
        members_names = [member.name for member in members]

        async with self.bot.database.get_session() as session:
            added_indices = await HabitueManager.sync_habitues(
                session, members_ids, members_with_role_habitue
            )

        # Retrieve the names of the added habitues
        added_habitues = [members_names[idx] for idx in added_indices]

        log.info(f"Added {len(added_habitues)} new habitues to the database.")
        log.debug(f"New habitues: {added_habitues}")


def setup(bot: ZORS):
    bot.add_cog(Habitue(bot))
