import discord
from discord.ext import commands


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(description="pings", guild_ids=[896903198172930058])
    async def ping(self, ctx, message: discord.Option(str, "message") = "pong"):
        await ctx.respond(f":ping_pong: {message} :ping_pong:")


def setup(bot):
    bot.add_cog(Ping(bot))
