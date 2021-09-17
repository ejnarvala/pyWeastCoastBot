from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.reply(":ping_pong: pong :ping_pong:")


def setup(bot):
    bot.add_cog(Ping(bot))
