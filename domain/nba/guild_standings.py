import attr


@attr.s
class GuildStandings:

    race_plot_df = attr.ib()
    leaderboard_df = attr.ib()
    nba_scoreboard_df = attr.ib()
