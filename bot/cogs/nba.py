import logging
import attr
from lib.utils.consts import NBA_WINS_POOL_SHEET_URL
from lib.utils.graph import generate_line_plot, write_fig_to_tempfile
from table2ascii import table2ascii
from discord import Colour, Embed, File
from discord.ext import commands
from domain.nba.guild_standings import GuildStandings
from domain.nba.nba_wins_pool_service import NbaWinsPoolService

service = NbaWinsPoolService()


class Nba(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def nba_wins_pool(self, ctx):
        guild_id = ctx.message.guild.id
        if not guild_id:
            raise Exception("Message not from within a guild")

        guild_standings = service.guild_standings(guild_id)
        user_ids = list(guild_standings.leaderboard_df["owner"])
        user_id_to_name = await self.get_user_names(user_ids)
        logging.info(user_id_to_name)
        response = NbaWinsPoolStandingsResponse(
            guild_standings=guild_standings, user_id_map=user_id_to_name
        )

        await ctx.reply(embed=response.to_embed(), file=response.wins_graph_file)

    async def get_user_names(self, user_ids):
        user_id_to_username = {}
        for user_id in user_ids:
            user = await self.bot.fetch_user(int(user_id))
            if user and user.display_name:
                user_id_to_username[user_id] = user.name
        return user_id_to_username


@attr.s
class NbaWinsPoolStandingsResponse:

    guild_standings: GuildStandings = attr.ib()
    user_id_map = attr.ib()

    @property
    def description(self):
        leaderboard_df = self.guild_standings.leaderboard_df

        leaderboard_df["name"] = leaderboard_df["owner"].map(self.user_id_map)
        leaderboard_df = leaderboard_df[["rank", "name", "wins", "losses"]]
        leaderboard_df = leaderboard_df.astype(str)
        ascii_table = table2ascii(
            header=leaderboard_df.columns.tolist(), body=leaderboard_df.values.tolist()
        )
        return f"```{ascii_table}```"

    @property
    def wins_graph_file(self):
        race_plot_df = self.guild_standings.race_plot_df
        owners = [str(user_id) for user_id in self.user_id_map.keys()]
        fig = generate_line_plot(race_plot_df, x=race_plot_df["date"], y=owners)
        fig.for_each_trace(lambda t: t.update(name=self.user_id_map.get(t.name, t.name)))
        fig.update_layout(xaxis_title="Date", yaxis_title="Wins", legend_title="Users")
        return File(write_fig_to_tempfile(fig), filename="image.png")

    @property
    def url(self):
        return NBA_WINS_POOL_SHEET_URL

    @property
    def color(self):
        return Colour.orange()

    @property
    def title(self):
        return "NBA Wins Pool Standings"

    def to_embed(self):
        embed = Embed(
            title=self.title,
            url=self.url,
            description=self.description,
            color=self.color,
        )
        embed.set_image(url="attachment://image.png")
        return embed


def setup(bot):
    bot.add_cog(Nba(bot))