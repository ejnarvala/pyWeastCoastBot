import logging
import datetime

from discord import Colour, Embed, File, slash_command, TextChannel
from discord.ext import commands, tasks
from discord.ui import InputText, Modal, View, button
from lib.fitbot.service import FitbotService, GuildWeeklyStats
from lib.utils.consts import HexColors
from lib.utils.errors import InvalidParameter
from lib.utils.graph import generate_line_plot, write_fig_to_tempfile
from lib.utils.types import hex_to_rgb


class Fitbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fitbot = FitbotService()
        self.post_leaderboard.start()
        logging.info("Fitbot cog started")

    def cog_unload(self):
        self.post_leaderboard.cancel()

    @slash_command(
        description="Instructions to authorize fitbot",
        guild_only=True,
    )
    async def fitbot_register(self, ctx):
        url = self.fitbot.auth_url()
        description = f"""
            1. Click on [this link]({url})
            2. Check all permissions unless you potentially want to break stuff
            3. Look at the url & copy the value for `code`
            4. Click 'Submit Code'
        """
        embed = Embed(
            title="Fitbot Registration",
            url=url,
            description=description,
            color=Colour.from_rgb(*hex_to_rgb(HexColors.FITBIT_BLUE)),
        )
        view = RegistrationView(self.fitbot)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @slash_command(description="Disconnect from Fitbot", guild_only=True)
    async def fitbot_disconnect(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild_id
        logging.info(f"{user_id}, {guild_id}")
        self.fitbot.disconnect_user(user_id, guild_id)

        await ctx.respond("You've been disconnected from Fitbot", ephemeral=True)

    async def _get_weekly_leaderboard_response(self, guild_id):
        stats = self.fitbot.get_guild_weekly_stats(guild_id)
        user_id_to_username = {}
        for user_id in stats.user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user and user.name:
                user_id_to_username[user_id] = user.display_name
        return WeeklyLeaderboardResponse(stats, user_id_to_username)

    @slash_command(description="Weekly fibit stats", guild_only=True)
    async def fitbot_leaderboard(self, ctx):
        guild_id = ctx.guild_id
        await ctx.defer()
        response = await self._get_weekly_leaderboard_response(guild_id)
        await ctx.followup.send(embed=response.to_embed(), file=response.image_file)

    @tasks.loop(time=datetime.time(16))
    async def post_leaderboard(self):
        logging.info("Posting fitbot leaderboards")
        guild_ids = self.fitbot.get_registered_guild_ids()
        logging.info(f"Guild ids: {guild_ids}")
        for guild_id in guild_ids:
            guild = await self.bot.fetch_guild(int(guild_id))
            channels = await guild.fetch_channels()
            logging.info(f"Guild id: {guild_id}, channels: {channels}")
            for channel in channels:
                if isinstance(channel, TextChannel) and channel.name == "fitbot":
                    logging.info(f"Posting to guild {guild.name}, channel {channel.name}")
                    response = await self._get_weekly_leaderboard_response(guild_id)
                    channel.send(embed=response.to_embed(), file=response.image_file)

    @post_leaderboard.before_loop
    async def before_poll(self):
        await self.bot.wait_until_ready()

    @post_leaderboard.error
    async def post_leaderboard_error(self, error):
        logging.info(f"Error occurred while posting fitbot leaderboard: {error}")


class RegistrationView(View):
    def __init__(self, fitbot) -> None:
        super().__init__()
        self.fitbot = fitbot

    @button(label="Submit Code")
    async def submit_callback(self, button, interaction):
        await interaction.response.send_modal(SubmitCodeModal(self.fitbot))


class SubmitCodeModal(Modal):
    def __init__(self, fitbot) -> None:
        super().__init__(title="Fitbot Registration Code")
        self.fitbot = fitbot
        self.add_item(InputText(label="code"))

    async def callback(self, interaction):
        code = self.children[0].value
        user_id = interaction.message.author.id
        guild_id = interaction.message.guild.id

        if self.fitbot.is_user_registered(user_id, guild_id):
            raise InvalidParameter("You're already registered!")

        self.fitbot.store_auth_token(user_id, guild_id, code)

        await interaction.response.send_message(
            "You've been successfully registered", ephemeral=True
        )

    async def on_error(self, error, interaction):
        logging.error(f"Fitbot Registration Error: {error}")
        await interaction.response.send_message(
            f"Fitbot Registration Error: {error}", ephemeral=True
        )


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
