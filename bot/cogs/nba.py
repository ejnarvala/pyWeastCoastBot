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

    async def cog_check(self, ctx):
        if ctx.message and not ctx.message.guild.id:
            ctx.send("Command must be called within a server")
            return False
        return True

    @commands.command()
    async def nba_wins_pool(self, ctx):
        guild_id = ctx.message.guild.id
        guild_standings = service.guild_standings(guild_id)
        user_ids = list(guild_standings.leaderboard_df["owner"])
        user_id_to_name = await self.get_user_names(user_ids)
        response = NbaWinsPoolStandingsResponse(
            guild_standings=guild_standings, user_id_map=user_id_to_name
        )

        await ctx.send(embed=response.to_embed(), file=response.wins_graph_file)

    @commands.command()
    async def nba_wins_pool_teams(self, ctx):
        guild_id = ctx.message.guild.id
        team_breakdown_df = service.guild_team_breakdown(guild_id)
        user_ids = set(team_breakdown_df.index.tolist())
        user_id_to_name = await self.get_user_names(user_ids)
        response = NbaWinsPoolTeamsResponse(
            user_id_map=user_id_to_name, team_breakdown_df=team_breakdown_df
        )
        await ctx.send(embed=response.to_embed())

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
        leaderboard_df["record"] = (
            leaderboard_df[["wins", "losses"]].astype(str).agg("-".join, axis=1)
        )
        leaderboard_df = leaderboard_df[["rank", "name", "record"]].astype(str)
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


@attr.s
class NbaWinsPoolTeamsResponse:

    user_id_map = attr.ib()
    team_breakdown_df = attr.ib()

    @property
    def url(self):
        return NBA_WINS_POOL_SHEET_URL

    @property
    def color(self):
        return Colour.orange()

    @property
    def title(self):
        return "NBA Wins Pool Teams"

    @property
    def fields(self):
        df = self.team_breakdown_df
        fields = []
        # does anyone know pandas?
        for user_id, user_name in self.user_id_map.items():
            teams = [
                dict(name=row["full_name"], wins=row["wins"], losses=row["losses"])
                for _, row in df[df.index == str(user_id)].iterrows()
            ]

            team_string = table2ascii(
                header=["Name", "W/L"],
                body=[
                    [team["name"], str(int(team["wins"])) + "-" + str(int(team["losses"]))]
                    for team in teams
                ],
            )
            team_string = f"```{team_string}```"

            fields.append((user_name, team_string, False))

        return fields

    def to_embed(self):
        embed = Embed(
            title=self.title,
            url=self.url,
            color=self.color,
        )
        for name, value, inline in self.fields:
            embed.add_field(name=name, value=value, inline=inline)
        return embed


def setup(bot):
    bot.add_cog(Nba(bot))
