from functools import cached_property
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

    @cached_property
    def all_teams(cls):
        return [cls._build_nba_team_from_bdl_team(team) for team in cls.client.all_teams()]

    @classmethod
    def games(cls, start_date):
        params = BallDontLieParams(start_date=start_date)
        for game in cls.client.games(params):
            yield NbaGame(
                id=game["id"],
                date=game["date"],
                home_team=cls._build_nba_team_from_bdl_team(game["home_team"]),
                home_team_score=game["home_team_score"],
                status=game["status"],
                visitor_team=cls._build_nba_team_from_bdl_team(game["visitor_team"]),
                visitor_team_score=game["visitor_team_score"],
            )

