from discord import Option, slash_command
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @slash_command(description="pings")
    async def ping(self, ctx, message: Option(str, "message") = "pong"):
        await ctx.respond(f":ping_pong: {message} :ping_pong:")


def setup(bot):
    bot.add_cog(Ping(bot))
