from discord import CategoryChannel
from discord.ext import commands
import discord
from main import ZORS
from loguru import logger as log

from model.managers import GameCategoryManager
from model.schemas import GameCategory


class Gaming(commands.Cog):
    class DiscordParty:
        owner: discord.Member
        members: list[discord.Member]

    def __init__(self, bot: ZORS):
        self.bot = bot

    async def get_game_channel_associations(
            self, ctx: discord.AutocompleteContext
    ) -> list[discord.OptionChoice]:
        """
        Get the game channels names with there ids associated from the database.
        Returns:
            A dictionary with the game channels names and their ids.
        """
        async with self.bot.database.get_session() as session:
            game_categories: list[GameCategory] = await GameCategoryManager.get_all(session)
            # Si aucune catégorie n'est trouvée, retourner un dictionnaire avec un message explicite
            if not game_categories:
                return [discord.OptionChoice(
                    name="No game categories found", value="0"
                )]
            return [
                discord.OptionChoice(
                    name=game_category.name,
                    value=str(game_category.id)
                )
                for game_category in game_categories
            ]

    @commands.slash_command(name="add_game", description="Add a game to the server.")
    @commands.has_permissions(manage_channels=True)
    @discord.option(name="game", description="The name of the game to add.")
    async def add_game(self, ctx: discord.ApplicationContext, game: str):
        """
        Add a game to the server.
        A game is a category of games that can be played by the users.
        The created category will have 3 channels:
        - A voice channel that dynamically creates voice channels for the users to join.
        - A forum channel where users can make small precise talks
        - A text channel where users can talk generally about the game.
        Args:
            game: The name of the game to add.
            ctx: The context of the command.

        Returns:

        """
        main_game_category: CategoryChannel | None = discord.utils.get(
            ctx.guild.categories, name="🎮 [Jeux]"
        )
        if main_game_category is None:
            await ctx.respond("The main game category does not exist.")
            log.info("The main game category does not exist. create it first.")
            return
        main_game_category_position: int = main_game_category.position
        game_category = await ctx.guild.create_category(
            "> " + game, position=main_game_category_position + 1
        )
        game_forum = await game_category.create_forum_channel("Forum")
        game_text = await game_category.create_text_channel("Chat")
        game_voice = await game_category.create_voice_channel("➕Add Party")
        async with self.bot.database.get_session() as session:
            await GameCategoryManager.add(
                session,
                game_category.id,
                game,
                game_forum.id,
                game_text.id,
                game_voice.id,
            )
        await ctx.respond(f"The game category {game} has been added.")
        log.info("The game category has been added.")

    @commands.slash_command(
        name="delete_game", description="Delete a game from the server."
    )
    @commands.has_permissions(manage_channels=True)
    @discord.option(
        name="game",
        description="The category of the game to delete.",
        autocomplete=get_game_channel_associations,
    )
    async def delete_game(self, ctx: discord.ApplicationContext, game: str):
        """
        Delete a game from the server.
        A game is a category of games that can be played by the users.
        The created category will have 3 channels:
        - A voice channel that dynamically creates voice channels for the users to join.
        - A forum channel where users can make small precise talks
        - A text channel where users can talk generally about the game.
        Args:
            game: The name of the game to delete.
            ctx: The context of the command.

        Returns:

        """
        game_category: CategoryChannel | None = discord.utils.get(
            ctx.guild.categories, id=int(game)
        )
        if game_category is None:
            await ctx.respond("This game category does not exist.", ephemeral=True)
            log.info("This game category does not exist.")
            return
        for channel in game_category.channels:
            await channel.delete()
        await game_category.delete()
        async with self.bot.database.get_session() as session:
            await GameCategoryManager.delete(session, game_category.id)
            await ctx.respond(f"The game category {game_category.name.split()[-1]} has been deleted.")
            log.info(f"The game category {game_category.name.split()[-1]} has been deleted.")


def setup(bot: ZORS):
    bot.add_cog(Gaming(bot))
