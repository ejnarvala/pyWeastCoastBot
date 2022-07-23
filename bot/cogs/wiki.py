import requests
from discord import slash_command, Option
from discord.ext import commands


class Wiki(commands.Cog):

    wiki_search_url = "https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&namespace=0&format=json&search="

    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Search for wikipedia links", debug_guilds=[896903198172930058])
    async def wiki(self, ctx, search_text: Option(str, "Title search term")):
        link = self.search_wiki_articles(search_text)
        if not link:
            raise f"Sorry, couldn't find article for '{search_text}'"
        await ctx.respond(link)

    @wiki.error()
    async def wiki_error(self, ctx, error):
        await ctx.respond(str(error.original), ephemeral=True)

    @classmethod
    def search_wiki_articles(cls, search_text):
        url = cls.wiki_search_url + search_text
        res = requests.get(url).json()
        try:
            link = res[3][0]
            return link
        except IndexError:
            pass


def setup(bot):
    bot.add_cog(Wiki(bot))
