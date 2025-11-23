import asyncio

import discord
from discord import CategoryChannel, Member, VoiceChannel, VoiceState
from discord.ext import commands
from loguru import logger as log

from main import ZORS
from model.managers import GameCategoryManager, PartyManager
from model.schemas import GameCategory
from utils.settings import settings

from utils.zors_cog import ZorsCog


class Gaming(ZorsCog):
    """
    Cog gérant les fonctionnalités liées aux jeux vidéo sur le serveur.
    Permet de créer des catégories de jeux avec des salons dédiés,
    et gère des salons vocaux dynamiques pour les parties.
    """

    category_role = "==RÔLES ACCES=="

    def __init__(self, bot: ZORS):
        self.bot = bot

    # region events

    @commands.Cog.listener()
    async def on_voice_state_update(  # may not be the good function
        self,
        member: Member,
        before: VoiceState,
        after: VoiceState,
    ):
        """
        Gère la création et suppression des salons vocaux dynamiques pour les parties.
        Délègue le traitement à des fonctions spécialisées.
        """
        # Appel à la fonction qui gère la logique des parties
        await self.party_logic(member, before, after)

    # endregion

    async def get_game_channel_associations(
        self, ctx: discord.AutocompleteContext
    ) -> list[discord.OptionChoice]:
        """
        Récupère les noms et IDs des catégories de jeux depuis la base de données.
        Utilisé pour l'autocomplétion des commandes slash.
        """
        async with self.bot.database.get_session() as session:
            game_categories: list[GameCategory] = await GameCategoryManager.get_all(
                session
            )
            if not game_categories:
                return [
                    discord.OptionChoice(
                        name="Aucune catégorie de jeu trouvée", value="0"
                    )
                ]
            return [
                discord.OptionChoice(
                    name=game_category.name, value=str(game_category.id)
                )
                for game_category in game_categories
            ]

    @commands.slash_command(name="add_game", description="Ajoute un jeu au serveur.")
    @commands.has_permissions(manage_channels=True)
    @discord.option(name="game", description="Le nom du jeu à ajouter.")
    async def add_game(self, ctx: discord.ApplicationContext, game: str):
        """
        Ajoute une catégorie de jeu au serveur avec ses salons dédiés.
        Crée une structure complète pour un jeu vidéo (forums, chat, salon vocal).
        Crée aussi un rôle Discord associé à la catégorie.
        """
        main_game_category: CategoryChannel | None = discord.utils.get(
            ctx.guild.categories, name="🎮 [Jeux]"
        )
        if main_game_category is None:
            await ctx.respond("La catégorie principale de jeux n'existe pas.")
            log.info("La catégorie principale de jeux n'existe pas. Créez-la d'abord.")
            return

        # Création de la structure du jeu
        main_game_category_position: int = main_game_category.position
        game_category = await ctx.guild.create_category(
            "> " + game, position=main_game_category_position + 1
        )
        game_forum = await game_category.create_forum_channel("Forum")
        game_text = await game_category.create_text_channel("Chat")
        game_voice = await game_category.create_voice_channel("➕Add Party")

        # Création du rôle Discord associé à la catégorie
        game_role = await ctx.guild.create_role(name=f"{game}", mentionable=True)

        # Configuration des permissions de la catégorie
        await game_category.set_permissions(
            ctx.guild.default_role,  # @everyone
            view_channel=False,  # Invisible par défaut
            read_messages=False,
        )
        await game_category.set_permissions(
            game_role,  # Le rôle du jeu
            view_channel=True,  # Visible pour ceux qui ont le rôle
            read_messages=True,
            send_messages=True,
            connect=True,
            speak=True,
        )

        # Enregistrement en base de données avec l'ID du rôle
        async with self.bot.database.get_session() as session:
            await GameCategoryManager.add(
                session,
                game_category.id,
                game,
                game_forum.id,
                game_text.id,
                game_voice.id,
                game_role.id,  # Ajout de l'ID du rôle
            )

        await ctx.respond(
            f"La catégorie de jeu {game} a été ajoutée avec le rôle associé. "
            f"Utilisez `/join_game` pour y accéder."
        )
        log.info(
            f"La catégorie de jeu {game} a été ajoutée avec le rôle {game_role.name} "
            f"et permissions configurées."
        )

    @commands.slash_command(
        name="delete_game", description="Supprime un jeu du serveur."
    )
    @commands.has_permissions(manage_channels=True)
    @discord.option(
        name="game",
        description="La catégorie du jeu à supprimer.",
        autocomplete=get_game_channel_associations,
    )
    async def delete_game(self, ctx: discord.ApplicationContext, game: str):
        """
        Supprime une catégorie de jeu du serveur et tous ses salons associés.
        Supprime aussi le rôle Discord associé à la catégorie.
        Nettoie également les données du jeu dans la base de données.
        """
        game_category: CategoryChannel | None = discord.utils.get(
            ctx.guild.categories, id=int(game)
        )
        if game_category is None:
            await ctx.respond("Cette catégorie de jeu n'existe pas.", ephemeral=True)
            log.info("Cette catégorie de jeu n'existe pas.")
            return

        # Suppression des salons et de la catégorie
        for channel in game_category.channels:
            await channel.delete()
        await game_category.delete()

        # Suppression du rôle associé à la catégorie
        async with self.bot.database.get_session() as session:
            # Récupérer la catégorie en base pour obtenir l'ID du rôle
            db_category = await GameCategoryManager.get_by_id(session, int(game))
            if db_category and db_category.role_id:
                role = ctx.guild.get_role(db_category.role_id)
                if role:
                    await role.delete(reason="Suppression de la catégorie de jeu")
                    log.info(f"Rôle {role.name} supprimé avec la catégorie.")

            # Suppression des données en base
            await GameCategoryManager.delete(session, int(game))
            await ctx.respond(
                f"La catégorie de jeu {game_category.name.removeprefix('> ')} et son rôle ont été supprimés."
            )
            log.info(
                f"La catégorie de jeu {game_category.name.removeprefix('> ')} et son rôle ont été supprimés."
            )

    @commands.slash_command(
        name="join_game", description="Rejoindre un jeu pour voir ses salons."
    )
    @commands.has_role(settings.config.roles.gamer.id)
    @discord.option(
        name="game",
        description="Le jeu à rejoindre.",
        autocomplete=get_game_channel_associations,
    )
    async def join_game(self, ctx: discord.ApplicationContext, game: str):
        """Permet à un utilisateur de rejoindre un jeu et d'obtenir accès aux salons."""
        if not isinstance(ctx.author, Member):
            await ctx.respond(
                "Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        async with self.bot.database.get_session() as session:
            game_category = await GameCategoryManager.get_by_id(session, int(game))
            if not game_category:
                await ctx.respond("Ce jeu n'existe pas.", ephemeral=True)
                return

            role = ctx.guild.get_role(game_category.role_id)
            if not role:
                await ctx.respond("Le rôle de ce jeu est introuvable.", ephemeral=True)
                log.error(
                    f"Rôle {game_category.role_id} introuvable pour {game_category.name}"
                )
                return

            if role in ctx.author.roles:
                await ctx.respond(
                    f"Vous avez déjà accès à {game_category.name}.", ephemeral=True
                )
                return

            await ctx.author.add_roles(role, reason="Rejoint le jeu via /join_game")
            await ctx.respond(
                f"Vous avez rejoint {game_category.name} ! 🎮", ephemeral=True
            )
            log.info(f"{ctx.author.display_name} a rejoint {game_category.name}")

    @commands.slash_command(
        name="leave_game",
        description="Quitter un jeu et perdre l'accès à ses salons.",
    )
    @commands.has_role(settings.config.roles.gamer.id)
    @discord.option(
        name="game",
        description="Le jeu à quitter.",
        autocomplete=get_game_channel_associations,
    )
    async def leave_game(self, ctx: discord.ApplicationContext, game: str):
        """Permet à un utilisateur de quitter un jeu et de perdre l'accès aux salons."""
        if not isinstance(ctx.author, Member):
            await ctx.respond(
                "Cette commande doit être utilisée dans un serveur.", ephemeral=True
            )
            return

        async with self.bot.database.get_session() as session:
            game_category = await GameCategoryManager.get_by_id(session, int(game))
            if not game_category:
                await ctx.respond("Ce jeu n'existe pas.", ephemeral=True)
                return

            role = ctx.guild.get_role(game_category.role_id)
            if not role:
                await ctx.respond("Le rôle de ce jeu est introuvable.", ephemeral=True)
                log.error(
                    f"Rôle {game_category.role_id} introuvable pour {game_category.name}"
                )
                return

            if role not in ctx.author.roles:
                await ctx.respond(
                    f"Vous n'avez pas accès à {game_category.name}.", ephemeral=True
                )
                return

            await ctx.author.remove_roles(role, reason="Quitté le jeu via /leave_game")
            await ctx.respond(f"Vous avez quitté {game_category.name}.", ephemeral=True)
            log.info(f"{ctx.author.display_name} a quitté {game_category.name}")

    async def party_logic(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        """
        Gère la logique des parties de jeu.
        Créé automatiquement un salon vocal quand un utilisateur rejoint le salon "Add Party".
        Supprime le salon vocal quand il devient vide.
        """
        # Création d'un salon temporaire
        if before.channel != after.channel and after.channel is not None:
            after_channel = after.channel  # Type narrowing helper
            async with self.bot.database.get_session() as session:
                # Vérifier si le salon rejoint est un salon "Add Party"
                game_categories: list[GameCategory] = await GameCategoryManager.get_all(
                    session
                )

                for game_category in game_categories:
                    if after_channel.id == game_category.voice_id:
                        # Récupérer les parties de l'utilisateur
                        user_parties = await PartyManager.get_by_owner(
                            session, member.id
                        )

                        # Vérifier s'il a déjà une partie dans cette catégorie
                        existing_party = next(
                            (
                                p
                                for p in user_parties
                                if p.game_category_id == game_category.id
                            ),
                            None,
                        )

                        if existing_party:
                            # Utiliser la partie existante
                            channel = self.bot.get_channel(existing_party.channel_id)
                            if channel and isinstance(
                                channel, (VoiceChannel, discord.StageChannel)
                            ):
                                await member.move_to(channel)
                                log.info(
                                    f"Déplacement de {member.display_name} vers sa partie existante"
                                )
                                return
                            else:
                                # Si le salon n'existe plus, le supprimer de la BDD
                                await PartyManager.delete(
                                    session, existing_party.channel_id
                                )

                        # Créer un nouveau salon vocal
                        category = after_channel.category
                        if isinstance(category, CategoryChannel):
                            party_name = f"{member.display_name}-party"
                            new_channel = await category.create_voice_channel(
                                party_name
                            )
                        else:
                            log.debug("La catégorie du salon n'est pas valide.")
                            return

                        # Enregistrer dans la BDD
                        await PartyManager.add(
                            session, game_category, party_name, member, new_channel.id
                        )

                        # Déplacer le membre
                        await member.move_to(new_channel)
                        log.info(
                            f"Salon '{party_name}' créé pour {member.display_name}"
                        )
                        break

        # Suppression d'un salon temporaire vide
        if before.channel is not None and (
            after.channel != before.channel or after.channel is None
        ):
            # Vérifier si c'est un salon de partie
            if before.channel.name.endswith(
                "-party"
            ) and not before.channel.name.startswith("➕"):
                # Attendre pour vérifier que le salon est vide
                await asyncio.sleep(0.5)

                if len(before.channel.members) == 0:
                    async with self.bot.database.get_session() as session:
                        # Supprimer la partie de la BDD
                        party = await PartyManager.get_by_channel_id(
                            session, before.channel.id
                        )
                        if party:
                            await PartyManager.delete(session, before.channel.id)

                        # Supprimer le salon
                        await before.channel.delete()
                        log.info(
                            f"Salon dynamique vide '{before.channel.name}' supprimé"
                        )


def setup(bot: ZORS):
    bot.add_cog(Gaming(bot))
