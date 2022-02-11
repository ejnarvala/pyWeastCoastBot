from datetime import datetime, timedelta
from functools import cached_property

import pandas as pd

from domain.nba.nba_game import NbaGame
from domain.nba.nba_team import NbaTeam
from lib.balldontlie.client import BallDontLieClient
from lib.balldontlie.params import BallDontLieParams


class NbaRepository:

    client = BallDontLieClient()

    @staticmethod
    def _build_nba_team_from_bdl_team(team):
        return NbaTeam(
            id=team["id"],
            city=team["city"],
            conference=team["conference"],
            full_name=team["full_name"],
            name=team["name"],
            abbreviation=team["abbreviation"],
        )

    @staticmethod
    def _build_nba_team_from_live_team(team):
        live_id_to_bdl_id = {
            1610612738: 2,  # Celtics
            1610612751: 3,  # Nets
            1610612752: 20,  # Knicks
            1610612755: 23,  # 76ers
            1610612761: 28,  # Raptors
            1610612741: 5,  # Bulls
            1610612739: 6,  # Cavs
            1610612765: 9,  # Pistons
            1610612754: 12,  # Pacers
            1610612749: 17,  # Bucks
            1610612737: 1,  # Hawks
            1610612766: 4,  # Hornets
            1610612748: 16,  # Heat
            1610612753: 22,  # Magic
            1610612764: 30,  # Wizards
            1610612743: 8,  # Nuggets
            1610612750: 18,  # Timberwolves
            1610612760: 21,  # Thunder
            1610612757: 25,  # Blazers
            1610612762: 29,  # Jazz
            1610612744: 10,  # Warriors
            1610612746: 13,  # Clippers
            1610612747: 14,  # Lakers
            1610612756: 24,  # Suns
            1610612758: 26,  # Kings
            1610612742: 7,  # Mavs
            1610612745: 11,  # Rockets
            1610612763: 15,  # Grizzlies
            1610612740: 19,  # Pelicans
            1610612759: 27,  # Spurs
        }
        return NbaTeam(
            id=live_id_to_bdl_id[team["teamId"]],
            city=team["teamCity"],
            conference="",
            full_name=" ".join([team["teamCity"], team["teamName"]]),
            name=team["teamName"],
            abbreviation=team["teamTricode"],
        )

    @cached_property
    def all_teams(cls):
        return [cls._build_nba_team_from_bdl_team(team) for team in cls.client.all_teams()]

    @classmethod
    def games(cls, start_date):
        live_date = None
        for game in cls.client.live_games():
            live_date = datetime.strptime(game["gameEt"][:10], '%Y-%m-%d')
            yield NbaGame(
                id=game["gameId"],
                date=pd.Timestamp(game["gameEt"]).date().strftime("%Y-%m-%d"),
                home_team=cls._build_nba_team_from_live_team(game["homeTeam"]),
                home_team_score=game["homeTeam"]["score"],
                status=game["gameStatusText"],
                visitor_team=cls._build_nba_team_from_live_team(game["awayTeam"]),
                visitor_team_score=game["awayTeam"]["score"]
            )
        # Use BallDontLie API only for games that aren't on today's scoreboard
        params = BallDontLieParams(start_date=start_date, end_date=live_date - timedelta(days=1))
        past_games = cls.client.games(params)
        for game in past_games:
            if game["id"] == 474073:
                game["home_team_score"] = 101
            yield NbaGame(
                id=game["id"],
                date=pd.Timestamp(game["date"]).date().strftime("%Y-%m-%d"),
                home_team=cls._build_nba_team_from_bdl_team(game["home_team"]),
                home_team_score=game["home_team_score"],
                status=game["status"],
                visitor_team=cls._build_nba_team_from_bdl_team(game["visitor_team"]),
                visitor_team_score=game["visitor_team_score"],
            )
