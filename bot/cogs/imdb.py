import logging

from lib.omdb.imdb_file import ImdbFilm
from discord.ext import commands
from discord import Embed
from lib.omdb.client import OmdbClient, OmdbError

class IMDB(commands.Cog):

    omdb_client = OmdbClient()

    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    async def imdb(self, ctx, *, title_search_text):
        film = self.omdb_client.find_by_title(title_search_text)
        logging.info(f"Found IMDB entry for search '{title_search_text}': {film}")
        await ctx.send(embed=self.embed_from_film(film))

    @imdb.error
    async def imdb_error(self, ctx, error):
        logging.error(f"IMDB Error: {error}")
        if isinstance(error.original, OmdbError):
            await ctx.reply(f"OMDB Error: {error.original}")

    @staticmethod
    def embed_from_film(film: ImdbFilm) -> Embed:
        embed = Embed(
            title=film.title,
            url=film.imdb_url,
            description=film.plot
        )
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