from discord.ext import commands


class Stonk(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


def setup(bot):
    bot.add_cog(Stonk(bot))
