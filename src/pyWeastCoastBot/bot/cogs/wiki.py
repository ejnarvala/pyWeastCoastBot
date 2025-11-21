import logging

import requests
from discord import Option, slash_command
from discord.ext import commands


class Wiki(commands.Cog):
    wiki_search_url = "https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&namespace=0&format=json&search="

    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="Search for wikipedia links")
    async def wiki(self, ctx, search_text: Option(str, "Title search term")):
        await ctx.defer()
        link = self.search_wiki_articles(search_text)
        if not link:
            await ctx.followup.send(f"Sorry, couldn't find article for '{search_text}'", ephemeral=True)
            return
        await ctx.followup.send(link)

    @classmethod
    def search_wiki_articles(cls, search_text):
        url = cls.wiki_search_url + search_text
        res = requests.get(url).json()
        try:
            link = res[3][0]
            return link
        except IndexError:
            pass

    @wiki.error
    async def wiki_error(self, ctx, error):
        logging.error(f"Wiki Error: {error}")
        await ctx.followup.send(str(error.original), ephemeral=True)


def setup(bot):
    bot.add_cog(Wiki(bot))
