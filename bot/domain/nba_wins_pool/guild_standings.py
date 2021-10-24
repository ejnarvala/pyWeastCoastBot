import attr


@attr.s
class GuildStandings:

    wins_per_day_image = attr.ib()
    leaderboard_df = attr.ib()
