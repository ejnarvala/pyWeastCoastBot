from django.core.management.base import BaseCommand
from db.models import UserWinPoolTeam
from domain.nba.nba_repository import NbaRepository

import logging

guild_id = 741484274150277130

team_id_to_auction_price = {
    1: 32,
    2: 65,
    3: 120,
    4: 21,
    5: 52,
    7: 65,
    8: 56,
    10: 82,
    12: 40,
    13: 32,
    14: 100,
    15: 33,
    16: 72,
    17: 99,
    18: 11,
    19: 10,
    20: 47,
    23: 68,
    24: 78,
    25: 42,
    26: 10,
    27: 6,
    28: 9,
    29: 66,
    30: 11,
}

user_id_to_team_names = {
    149768200941207552: ["Wizards", "Hawks", "Nets", "Trail Blazers", "Clippers"],  # ejnar
    235986434501115904: ["Warriors", "Bulls", "Spurs", "Lakers", "Pelicans"],  # sharan
    282245321906716682: ["Nuggets", "Knicks", "Heat", "Kings", "Celtics"],  # rishi
    282300873755983872: ["Jazz", "Timberwolves", "Bucks", "Raptors", "Mavericks"],  # sup
    525530793351839744: ["Hornets", "Grizzlies", "76ers", "Suns", "Pacers"],  # jos
}

user_id_to_user = {
    149768200941207552: "Ejnar",
    235986434501115904: "Sharan",
    282245321906716682: "Rishi",
    282300873755983872: "Sup",
    525530793351839744: "Josiah",
}

nba_repo = NbaRepository()


class Command(BaseCommand):
    def handle(self, **options):
        all_teams = nba_repo.all_teams

        team_name_to_id = {team.name: team.id for team in all_teams}

        for user_id, team_names in user_id_to_team_names.items():
            logging.info(f"Processing {user_id_to_user[user_id]} - {team_names}")

            if len(team_names) < 5:
                logging.info(
                    f"User {user_id_to_user[user_id]} does not have 5 teams, teams: {team_names.keys()}"
                )

            for team_name in team_names:
                team_id = team_name_to_id[team_name]
                try:
                    UserWinPoolTeam.objects.create(
                        user_id=user_id,
                        guild_id=guild_id,
                        bdl_team_id=team_id,
                        team_name=team_name,
                        auction_price=team_id_to_auction_price[team_id],
                    )
                except Exception as e:
                    logging.info(
                        f"Could not create entry for user: {user_id_to_user[user_id]}, team: {team_name} - {e}"
                    )
