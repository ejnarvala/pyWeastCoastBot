import datetime
import logging

from discord import Colour, Embed, File
from discord.commands import SlashCommandGroup
from discord.ext import commands, tasks
from discord.ui import InputText, Modal, View, button

from pyWeastCoastBot.lib.fitbot.service import FitbotService, GuildWeeklyStats
from pyWeastCoastBot.utils.consts import HexColors
from pyWeastCoastBot.utils.graph import generate_line_plot_image
from pyWeastCoastBot.utils.types import hex_to_rgb


class Fitbot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fitbot = FitbotService()
        self.post_leaderboard.start()
        logging.info("Fitbot cog started")

    def cog_unload(self):
        self.post_leaderboard.cancel()

    fitbot = SlashCommandGroup("fitbot", "Google Health integration commands", guild_only=True)

    @fitbot.command(name="register", description="Instructions to authorize fitbot")
    async def fitbot_register(self, ctx):
        url = self.fitbot.auth_url(ctx.author.id, ctx.guild_id)
        description = (
            f"1. Link or migrate your Fitbit account in the Google Health app\n"
            f"2. Click on [this link]({url}) and grant activity and fitness access\n"
            f"3. You'll be redirected to a page showing your authorization code\n"
            f"4. Click 'Copy to Clipboard' on that page\n"
            f"5. Return here and click 'Submit Code' below\n"
            f"Your activity data may appear in this server's Fitbot leaderboard."
        )
        embed = Embed(
            title="Fitbot Registration",
            url=url,
            description=description,
            color=Colour.from_rgb(*hex_to_rgb(HexColors.FITBIT_BLUE)),
        )
        view = RegistrationView(self.fitbot)
        await ctx.respond(embed=embed, view=view, ephemeral=True)

    @fitbot.command(name="disconnect", description="Disconnect from Fitbot")
    async def fitbot_disconnect(self, ctx):
        user_id = ctx.author.id
        guild_id = ctx.guild_id
        logging.info(f"{user_id}, {guild_id}")
        await self.fitbot.disconnect_user(user_id, guild_id)

        await ctx.respond("You've been disconnected from Fitbot", ephemeral=True)

    async def _get_weekly_leaderboard_response(self, guild_id):
        stats = await self.fitbot.get_guild_weekly_stats(guild_id)
        user_id_to_username = {}
        for user_id in stats.user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user and user.name:
                user_id_to_username[user_id] = user.display_name
        return WeeklyLeaderboardResponse(stats, user_id_to_username)

    @fitbot.command(name="leaderboard", description="Weekly Google Health activity stats")
    async def fitbot_leaderboard(self, ctx):
        guild_id = ctx.guild_id
        await ctx.defer()
        response = await self._get_weekly_leaderboard_response(guild_id)
        await ctx.followup.send(embed=response.to_embed(), file=response.image_file)

    @tasks.loop(time=datetime.time(19))
    async def post_leaderboard(self):
        logging.info("Posting fitbot leaderboards")
        guild_ids = await self.fitbot.get_registered_guild_ids()
        logging.info(f"Guild ids: {guild_ids}")
        for guild_id in guild_ids:
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                logging.warning(f"Skipping Fitbot leaderboard for uncached guild {guild_id}")
                continue

            channels = [channel for channel in guild.text_channels if "fitbot" in channel.name]
            if not channels:
                logging.error(f"No compatible Fitbot text channel found for guild {guild_id}")
                continue

            for channel in channels:
                logging.info(f"Posting to guild {guild.name}, channel {channel.name}")
                response = await self._get_weekly_leaderboard_response(guild_id)
                await channel.send(embed=response.to_embed(), file=response.image_file)

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
        user_id = interaction.user.id
        guild_id = interaction.guild_id

        await self.fitbot.store_auth_token(user_id, guild_id, code)

        await interaction.response.send_message("You've been successfully registered", ephemeral=True)

    async def on_error(self, error, interaction):
        logging.error(f"Fitbot Registration Error: {error}")
        await interaction.response.send_message(f"Fitbot Registration Error: {error}", ephemeral=True)


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
            return "This server has no registered Google Health accounts"

        description = "**Weekly Active Minutes**"
        for index, entry in enumerate(self.guild_stats.weekly_active_minutes_leaderboard, start=1):
            description += f"\n{index}. <@!{entry.user_id}>: {entry.score}"

        description += "\n\n**Weekly Steps**"
        for index, entry in enumerate(self.guild_stats.weekly_steps_leaderboard, start=1):
            description += f"\n{index}. <@!{entry.user_id}>: {entry.score}"

        description += "\n\n**Last Day Steps**"
        for index, entry in enumerate(self.guild_stats.last_day_steps_leaderboard, start=1):
            description += f"\n{index}. <@!{entry.user_id}>: {entry.score}"
        return description

    @property
    def thumbnail_image_url(self):
        return "https://img.icons8.com/color/96/fitbit.png"

    @property
    def image_file(self):
        df = self.guild_stats.steps_df
        renamed_df = df.rename(columns=lambda column: self.user_id_map.get(str(column), str(column)))
        return File(
            generate_line_plot_image(
                renamed_df,
                x=renamed_df.index,
                y=list(renamed_df.columns),
                xlabel="Date",
                ylabel="Steps",
                legend_title="Users",
                show_markers=True,
                show_y_grid=True,
                date_format="%b %d",
                convert_timezone=False,
            ),
            filename="image.png",
        )

    def to_embed(self):
        embed = Embed(title="FitBot Leaderboard", description=self.description, color=self.color)
        embed.set_thumbnail(url=self.thumbnail_image_url)
        embed.set_image(url="attachment://image.png")
        return embed


def setup(bot):
    bot.add_cog(Fitbot(bot))
