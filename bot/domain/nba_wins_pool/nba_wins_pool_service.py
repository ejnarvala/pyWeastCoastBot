from collections import defaultdict
from datetime import datetime
from functools import cached_property

import pandas as pd
from db.models import UserWinPoolTeam
from domain.nba_wins_pool.guild_standings import GuildStandings
from lib.balldontlie.client import NbaRepository
from lib.utils.graph import generate_line_plot_image

SEASON_START_DATE_2021 = datetime(2021, 10, 18)  # TODO update this next year(FY2023)


class NbaWinsPoolService:

    nba_repo = NbaRepository()

    @cached_property
    @classmethod
    def current_seasons_completed_games(cls):
        this_seasons_games = []
        games = cls.nba_repo.games(start_date=SEASON_START_DATE_2021)
        for game in games:
            if game.status != "Final":
                break
            this_seasons_games.append(game)

        return this_seasons_games

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

        games_df = cls.gen_games_df(cls.current_seasons_completed_games, team_id_to_user_id)

        wins_per_day_df = cls.build_race_plot_df(games_df, team_id_to_user_id)
        leaderboard_df = cls.build_leaderboard_df(games_df, team_id_to_user_id)

        wins_per_day_image = generate_line_plot_image(
            wins_per_day_df, x=wins_per_day_df.index, y=list(wins_per_day_df.columns)
        )

        return GuildStandings(
            wins_per_day_image=wins_per_day_image,
            leaderboard_df=leaderboard_df,
        )

    @classmethod
    def guild_team_breakdown(cls, guild_id):
        user_teams = cls.get_guild_user_teams(guild_id)

        team_id_to_user_id = {user_team.bdl_team_id: user_team.user_id for user_team in user_teams}

        team_id_to_price = {
            user_team.bdl_team_id: user_team.auction_price for user_team in user_teams
        }

        user_ids = set(user_team.user_id for user_team in user_teams)

        games_df = cls.gen_games_df(cls.current_seasons_completed_games, team_id_to_user_id)
        teams_df = cls.gen_teams_df(cls.nba_repo.all_teams, team_id_to_price)
        return cls.build_team_breakdown_df(
            games_df, teams_df, team_id_to_user_id, team_id_to_price, user_ids
        )

    # @classmethod
    # def _wins_per_day_df(cls, games, team_id_to_user_id):
    #     date_to_games = defaultdict(list)
    #     for game in games:
    #         date_to_games[game.date].append(game)

    #     wins_per_day = defaultdict(list)
    #     for _, day_games in date_to_games:
    #         daily_wins = defaultdict(int)
    #         for day_game in day_games:
    #             home_user_id = team_id_to_user_id.get(day_game.home_team.id)
    #             visitor_user_id = team_id_to_user_id.get(day_game.visitor_team.id)
    #             if day_game.home_team_score > day_games.visitor_team_score:
    #                 daily_wins[home_user_id] += 1
    #             else:
    #                 daily_wins[visitor_user_id] += 1
    #         wins_per_day.append(daily_wins)

    #     return pd.DataFrame(wins_per_day)

    # @classmethod
    # def _user_win_loss_total_df(cls, games, team_id_to_user_id):
    #     wins = defaultdict(int)
    #     losses = defaultdict(int)
    #     for game in games:
    #         home_user_id = team_id_to_user_id.get(game.home_team.id)
    #         visitor_user_id = team_id_to_user_id.get(game.visitor_team.id)
    #         if game.home_team_score > games.visitor_team_score:
    #             wins[home_user_id] += 1
    #             losses[visitor_user_id] += 1
    #         else:
    #             losses[home_user_id] += 1

    #     # instead of deleting could add 'teams not in pool' W/L
    #     del wins[None]
    #     del losses[None]
    #     df = pd.DataFrame(dict(wins=wins, losses=losses))
    #     df.reset_index()
    #     return df.reset_index().rename(columns=dict(index='user_id'))

    # @classmethod
    # def _standings_df(cls, games, team_id_to_user_id):
    #     wins_losses_df = cls.user_win_loss_total_df(games, team_id_to_user_id)
    #     ranked_wins_losses_df = wins_losses_df.sort_values(
    #         by=['wins'], ascending=False, ignore_index=True, inplace=True
    #     )
    #     ranked_wins_losses_df['rank'] = ranked_wins_losses_df.index + 1
    #     return ranked_wins_losses_df

    # @classmethod
    # def build_standings_df(cls, games, team_id_to_user_id):
    #     games_df = cls.gen_games_df(games, team_id_to_user_id)
    #     wins_losses_df = cls.build_leaderboard_df(games_df)
    #     wins_losses_df = wins_losses_df.reset_index().rename(columns=dict(index='user_id'))
    #     ranked_wins_losses_df = wins_losses_df.sort_values(
    #         by=['wins'], ascending=False, ignore_index=True, inplace=True
    #     )
    #     ranked_wins_losses_df['rank'] = ranked_wins_losses_df.index + 1
    #     return ranked_wins_losses_df

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

        df = pd.DataFrame.from_records([game.to_dict() for game in games])

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
        team_records = [team.to_dict() for team in teams]
        teams_df = pd.DataFrame.from_records(team_records).set_index("id", drop=False)
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
            .rename(columns=dict(index="user_id"))
            .sort_values(by=["wins", "losses"], ascending=[False, True], ignore_index=True)
        )

        leaderboard_df["rank"] = leaderboard_df.index + 1

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
    def build_race_plot_df(game_data_df, leaderboard_df):
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
        for owner in leaderboard_df.index:
            race_plot_df = race_plot_df.merge(
                race_plot_counts[:, owner].cumsum().rename(owner),
                how="left",
                left_on="date",
                right_on="date",
            )

        return race_plot_df.fillna(method="ffill").fillna(0)
