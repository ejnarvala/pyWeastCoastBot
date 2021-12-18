import logging
import re
from datetime import datetime

import pandas as pd

from db.models import UserWinPoolTeam
from domain.nba.guild_standings import GuildStandings
from domain.nba.nba_repository import NbaRepository

SEASON_START_DATE_2021 = datetime(2021, 10, 18)  # TODO update this next year(FY2023)


class NbaWinsPoolService:

    nba_repo = NbaRepository()

    @classmethod
    def current_seasons_games(cls):
        return list(
            cls.nba_repo.games(start_date=SEASON_START_DATE_2021)
        )
        
    @classmethod
    def get_guild_user_teams(cls, guild_id):
        user_teams = UserWinPoolTeam.objects.filter(guild_id=guild_id)
        if not user_teams:
            raise Exception("No users/teams in this server")
        return user_teams

    @classmethod
    def guild_standings(cls, guild_id):
        user_teams = cls.get_guild_user_teams(guild_id)

        team_id_to_user_id = {user_team.bdl_team_id: user_team.user_id for user_team in user_teams}

        games = cls.current_seasons_games()
        games_df = cls.gen_games_df(games, team_id_to_user_id)
        leaderboard_df = cls.build_leaderboard_df(games_df)
        owners = leaderboard_df["owner"].tolist()
        race_plot_df = cls.build_race_plot_df(games_df, owners)
        scoreboard_df = cls.build_scoreboard_df(games_df)

        return GuildStandings(
            race_plot_df=race_plot_df,
            leaderboard_df=leaderboard_df,
            nba_scoreboard_df=scoreboard_df
        )

    @classmethod
    def guild_team_breakdown(cls, guild_id):
        user_teams = cls.get_guild_user_teams(guild_id)

        team_id_to_user_id = {user_team.bdl_team_id: user_team.user_id for user_team in user_teams}

        team_id_to_price = {
            user_team.bdl_team_id: user_team.auction_price for user_team in user_teams
        }

        user_ids = set(user_team.user_id for user_team in user_teams)
        games = cls.current_seasons_games()
        logging.info(games)

        games_df = cls.gen_games_df(games, team_id_to_user_id)
        teams_df = cls.gen_teams_df(cls.nba_repo.all_teams, team_id_to_price)
        return cls.build_team_breakdown_df(
            games_df, teams_df, team_id_to_user_id, team_id_to_price, user_ids
        )

    @staticmethod
    def gen_games_df(games, team_id_to_owner):
        """
        Pull game data from API and determine winners

        Parameters
        ----------
        games: list
            list of nba games to generate df for
        team_id_to_owner: dict
            mapping of team id to owner
        """
        data = pd.json_normalize([game.to_dict() for game in games])
        df = pd.DataFrame(data)
        df["winning_team_id"] = df["home_team.id"].where(
            (df.status == "Final") & (df.home_team_score > df.visitor_team_score),
            other=df["visitor_team.id"].where(df.status == "Final"),
        )
        df["losing_team_id"] = df["home_team.id"].where(
            (df.status == "Final") & (df.home_team_score < df.visitor_team_score),
            other=df["visitor_team.id"].where(df.status == "Final"),
        )
        df["winning_owner"] = df["winning_team_id"].apply(
            lambda x: team_id_to_owner.get(str(int(x))) if pd.notnull(x) else pd.NA
        )
        df["losing_owner"] = df["losing_team_id"].apply(
            lambda x: team_id_to_owner.get(str(int(x))) if pd.notnull(x) else pd.NA
        )

        return df

    @staticmethod
    def gen_teams_df(teams, team_id_to_price):
        """
        Get team data from API and map auction prices
        Parameters
        ----------
        teams: list
            list of NbaTeams
        team_id_to_price: dict
            output of get_team_auction()

        Returns
        -------
        pandas DataFrame of all NBA teams
        """
        data = pd.json_normalize([team.to_dict() for team in teams])
        teams_df = pd.DataFrame(data).set_index("id", drop=False)
        teams_df["auction_price"] = teams_df["id"].astype(str).map(team_id_to_price)

        return teams_df

    @staticmethod
    def build_leaderboard_df(game_data_df):
        """
        Build leaderboard dataframe of each owner and total number of wins/losses

        Parameters
        ----------
        game_data_df: pandas DataFrame
            output of gen_game_df()

        Returns
        -------
        pandas DataFrame of owners, showing their total wins/losses
        """
        df = game_data_df
        leaderboard_df = pd.DataFrame(
            {
                "wins": df.groupby("winning_owner")["id"].count(),
                "losses": df.groupby("losing_owner")["id"].count(),
            }
        )
        leaderboard_df = (
            leaderboard_df.reset_index()
            .rename(columns=dict(index="owner"))
            .sort_values(by=["wins", "losses"], ascending=[False, True], ignore_index=True)
        )

        leaderboard_df["rank"] = (
            leaderboard_df["wins"].rank(method="min", ascending=False).astype(int)
        )

        return leaderboard_df

    @staticmethod
    def build_team_breakdown_df(game_data_df, teams_df, team_id_to_owner, team_id_to_price, owners):
        """
        Build dataframe showing W-L records for each team, grouped by owner

        Parameters
        ----------
        game_data_df: pandas DataFrame
            output of gen_game_df()
        teams_df: pandas DataFrame
            output of gen_teams_df()
        team_id_to_owner: dict
            output of get_team_owner()
        team_id_to_price: dict
            output of get_team_auction()
        owners: list
            list of owners to consider

        Returns
        -------
        pandas DataFrame
        """
        df = game_data_df
        nba_standings_df = pd.DataFrame(
            {
                "wins": df.groupby("winning_team_id")["id"].count(),
                "losses": df.groupby(["losing_team_id"])["id"].count(),
            }
        ).fillna(0)
        nba_standings_df.index = nba_standings_df.index.astype(int)

        team_breakdown_df = nba_standings_df.join(teams_df[["id", "full_name"]])
        # look into getting owner & price from teams_df
        team_breakdown_df["owner"] = team_breakdown_df["id"].astype(str).map(team_id_to_owner)
        team_breakdown_df["auction_price"] = (
            team_breakdown_df["id"].astype(str).map(team_id_to_price)
        )

        team_breakdown_df = team_breakdown_df.drop(columns="id")[
            ["owner", "full_name", "wins", "losses", "auction_price"]
        ]

        team_breakdown_df = team_breakdown_df.sort_values(
            by=["wins", "losses", "auction_price"], ascending=[False, True, False]
        )
        team_breakdown_df = team_breakdown_df.set_index("owner")

        return team_breakdown_df.loc[owners]

    @staticmethod
    def build_race_plot_df(game_data_df, owners):
        """
        Generate dataframe showing cumulative wins per owner by date

        Parameters
        ----------
        game_data_df: pandas DataFrame
            output of gen_game_df()
        leaderboard_df: pandas DataFrame
            output of build_leaderboard_df()

        Returns
        -------
        pandas DataFrame
        """
        df = game_data_df
        race_plot_counts = df.groupby(["date", "winning_owner"])["id"].count()
        race_plot_df = pd.DataFrame(
            race_plot_counts.index.get_level_values(0)
            .unique()
            .insert(0, pd.to_datetime("2021-10-18", utc=True))
        )
        for owner in owners:
            race_plot_df = race_plot_df.merge(
                race_plot_counts[:, owner].cumsum().rename(owner),
                how="left",
                left_on="date",
                right_on="date",
            )

        return race_plot_df.fillna(method="ffill").fillna(0)

    @staticmethod
    def build_scoreboard_df(game_data_df):
        df = game_data_df
        df["score"] = df.apply(generate_score_str, axis=1)
        todays_games = df[(df["date"].max().month == df["date"].dt.month) & (df["date"].max().day == df["date"].dt.day)]
        return todays_games.sort_values(by="status")[["status", "score"]]


def generate_score_str(scoreboard_row):
    home_tm = scoreboard_row["home_team.abbreviation"]
    away_tm = scoreboard_row["visitor_team.abbreviation"]
    home_score = scoreboard_row["home_team_score"]
    away_score = scoreboard_row["visitor_team_score"]
    status = scoreboard_row["status"]

    if re.match("^[0-9|P]", status):
        # Game hasn't started or is postponed, don't show score
        score = f"{home_tm} vs. {away_tm}"
    else:
        score = f"{home_tm} {home_score}, {away_tm} {away_score}"
    return score
