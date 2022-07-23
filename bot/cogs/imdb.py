import logging

from discord import Embed, slash_command, Option
from discord.ext import commands
from lib.omdb.client import OmdbClient, OmdbError
from lib.omdb.imdb_file import ImdbFilm
from lib.utils.errors import InvalidParameter


class IMDB(commands.Cog):

    omdb_client = OmdbClient()

    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Search IMDB by film title")
    async def imdb(
        self,
        ctx,
        title_search_text: Option(str, "Title search term") = None,
        imdb_id: Option(str, "IMDb ID") = None,
        year: Option(int, "Year") = None,
    ):
        if not (title_search_text or imdb_id):
            raise InvalidParameter("title or IMDb ID required")
        film = self.omdb_client.find_by_title_or_id(
            title=title_search_text, imdb_id=imdb_id, year=year
        )
        logging.info(
            f"Found IMDB entry for search title={title_search_text},"
            f"imdb_id={imdb_id}, year={year}: {film}"
        )
        await ctx.respond(embed=self.embed_from_film(film))

    @imdb.error
    async def imdb_error(self, ctx, error):
        logging.error(f"IMDB Error: {error}")
        await ctx.respond(str(error.original), ephemeral=True)

    @staticmethod
    def embed_from_film(film: ImdbFilm) -> Embed:
        embed = Embed(title=film.title, url=film.imdb_url, description=film.plot)
        embed.set_image(url=film.image_url)
        embed.add_field(name="Released", value=film.released, inline=True)
        embed.add_field(name="Genre", value=film.genre, inline=True)
        embed.add_field(name="Director", value=film.director, inline=True)
        embed.add_field(name="Actors", value=film.actors, inline=True)
        embed.add_field(name="Writers", value=film.writer, inline=True)
        embed.add_field(name="Runtime", value=film.runtime, inline=True)
        embed.add_field(name="ID", value=film.imdb_id, inline=True)
        embed.add_field(name="Rating", value=film.rating, inline=True)
        return embed


def setup(bot):
    bot.add_cog(IMDB(bot))
