from discord.ext import commands
import requests

class Wiki(commands.Cog):

    wiki_search_url = "https://en.wikipedia.org/w/api.php?action=opensearch&limit=1&namespace=0&format=json&search="

    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(brief="Search for wikipedia links")
    async def wiki(self, ctx, *, search_text):
        link = self.search_wiki_articles(search_text)
        message = link or f"Sorry, couldn't find article for '{search_text}'"
        await ctx.send(message)

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