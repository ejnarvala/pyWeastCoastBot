import logging

from discord import Colour, Embed, File
from discord.ext import commands
from fitbit.api import Fitbit

from lib.fitbot.service import FitbotService, GuildWeeklyStats
from lib.fitbot.config import FitbotConfig
from lib.utils.consts import HexColors
from lib.utils.graph import generate_line_plot_image, generate_line_plot, write_fig_to_tempfile
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
        description = f"""
                1. Click on [this link]({url})
                2. Check all permissions unless you potentially want to break stuff
                3. Look at the url & copy the value for `code`
                4. Call `/fitbot_register <code>`
            """
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
    async def fitbot_leaderboard(self, ctx):
        stats = self.fitbot.get_guild_weekly_stats(ctx.message.guild.id)
        user_id_to_username = {}
        for user_id in stats.user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user and user.name:
                user_id_to_username[user_id] = user.display_name
        response = WeeklyLeaderboardResponse(stats, user_id_to_username)
        await ctx.send(embed=response.to_embed(), file=response.image_file)

    @fitbot_register.error
    async def fitbot_register_error(self, ctx, error):
        logging.error(f"Fitbot Registration Error: {error}")
        await ctx.send(f"Fitbot Error: {error.original}")


class WeeklyLeaderboardResponse:
    def __init__(self, guild_stats: GuildWeeklyStats, user_id_map):
        self.guild_stats = guild_stats
        self.user_id_map = user_id_map

    @property
    def color(self):
        return Colour.from_rgb(*hex_to_rgb(HexColors.FITBIT_BLUE))

    @property
    def description(self):
        if not self.guild_stats.user_ids:
            return "This server has no registered fitbit accounts"

        am_lb = self.guild_stats.weekly_active_minutes_leaderboard
        description = "**Weekly Active Minutes**"
        for idx, lb_entry in enumerate(am_lb, start=1):
            description += f"\n{idx}. <@!{lb_entry.user_id}>: {lb_entry.score}"

        weekly_steps_lb = self.guild_stats.weekly_steps_leaderboard
        description += "\n\n**Weekly Steps**"
        for idx, lb_entry in enumerate(weekly_steps_lb, start=1):
            description += f"\n{idx}. <@!{lb_entry.user_id}>: {lb_entry.score}"

        last_day_steps_lb = self.guild_stats.last_day_steps_leaderboard
        description += "\n\n**Last Day Steps**"
        for idx, lb_entry in enumerate(last_day_steps_lb, start=1):
            description += f"\n{idx}. <@!{lb_entry.user_id}>: {lb_entry.score}"

        return description

    @property
    def thumbnail_image_url(self):
        return "https://icon-library.com/images/fitbit-icon/fitbit-icon-20.jpg"

    @property
    def image_file(self):
        df = self.guild_stats.steps_df
        fig = generate_line_plot(df, x=df.index, y=list(df.columns))
        fig.for_each_trace(lambda t: t.update(name=self.user_id_map.get(t.name, t.name)))
        fig.update_layout(xaxis_title="Date", yaxis_title="Steps", legend_title="Users")
        return File(write_fig_to_tempfile(fig), filename="image.png")

    def to_embed(self):
        embed = Embed(title="Fitbit Leaderboard", description=self.description, color=self.color)
        embed.set_thumbnail(url=self.thumbnail_image_url)
        embed.set_image(url="attachment://image.png")
        return embed


def setup(bot):
    bot.add_cog(Fitbot(bot))
