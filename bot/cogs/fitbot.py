import logging

from discord import Colour, Embed
from discord.ext import commands
from fitbit.api import Fitbit

from lib.fitbot.client import FitbotService
from lib.fitbot.config import FitbotConfig
from lib.utils.consts import HexColors
from lib.utils.types import hex_to_rgb


class Fitbot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.unauth_fitbit = Fitbit(
            FitbotConfig.client_id,
            FitbotConfig.client_secret,
            timeout=10,
        )
        self.fitbot = FitbotService()

    @commands.command(description="Instructions to authorize fitbot")
    async def fitbot_auth(self, ctx):
        url = self.fitbot.auth_url()
        description = (
            f"""
                1. Click on [this link]({url})
                2. Check all permissions unless you potentially want to break stuff
                3. Look at the url & copy the value for `code`
                4. Call `/fitbot_register <code>`
            """
        )
        embed = Embed(
            title="Fitbot Registration",
            url=url,
            description=description,
            color=Colour.from_rgb(*hex_to_rgb(HexColors.FITBIT_BLUE)),
        )
        await ctx.reply(embed=embed)

    @commands.command(description="Link Fitbit to Fitbot")
    async def fitbot_register(self, ctx, code):
        user_id = ctx.message.author.id
        if not ctx.message.guild:
            await ctx.reply("Cannot register outside of a server")
            return
        guild_id = ctx.message.guild.id

        if self.fitbot.is_user_registered(user_id, guild_id):
            await ctx.reply("You're already registered!")
            return

        self.fitbot.store_auth_token(user_id, guild_id, code)
        await ctx.reply("You've been successfully registered")

    @commands.command(description="Disconnect Fitbit from Fitbot")
    async def fitbot_disconnect(self, ctx):
        user_id = ctx.message.user.id
        if not ctx.message.guild:
            await ctx.reply("Cannot disconnect outside of a server")
            return
        guild_id = ctx.message.guild.id

        self.fitbot.disconnect_user(user_id, guild_id)

        await ctx.reply("You've been disconnected from Fitbot")

    @commands.command(description="Get Fitbit stats")
    async def fitbot_stats(self, ctx):
        pass

    @fitbot_register.error
    async def fitbot_register_error(self, ctx, error):
        logging.error(f"Fitbot Registration Error: {error}")
        await ctx.send(f"Fitbot Error: {error.original}")


def setup(bot):
    bot.add_cog(Fitbot(bot))
