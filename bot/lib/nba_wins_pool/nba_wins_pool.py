import json
import requests
from datetime import date

import pandas as pd

team_owner_json = "nba_wins_pool/team_owner.json"
team_auction_price_json = "nba_wins_pool/team_auction_price.json"

GAMES_URL = "https://www.balldontlie.io/api/v1/games"
TEAMS_URL = "https://www.balldontlie.io/api/v1/teams"


def get_team_owner():
    """
    Load mapping between teams and owners
    """
    with open(team_owner_json) as f:
        team_id_to_owner = json.load(f)
    return team_id_to_owner


def get_team_auction():
    """
    Load mapping between teams and auction values
    """
    with open(team_auction_price_json) as f:
        team_id_to_price = json.load(f)
    return team_id_to_price


def get_game_data(team_id_to_owner):
    """
    Pull game data from API and determine winners

    Parameters
    ----------
    team_id_to_owner: dict
        mapping of teams to owners, output of get_team_owner()
    """
    today = date.today()

    params = {
        "per_page": 100,
        "seasons[]": "2021",
        "start_date": "2021-10-19",
        "end_date": today.strftime("%Y-%m-%d"),
    }

    r = requests.get(GAMES_URL, params=params)

    data = r.json()

    total_pages = data["meta"]["total_pages"]
    # next_page = data["meta"]["next_page"]

    json_data = [data]

    for i in range(2, total_pages + 1):
        params["page"] = i
        r = requests.get(GAMES_URL, params=params)
        json_data.append(r.json())

    dfs = []
    for data in json_data:
        dfs.append(pd.DataFrame(pd.json_normalize(data["data"])))
    df = pd.concat(dfs)

    df["date"] = pd.to_datetime(df["date"])

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


def get_team_data(team_id_to_price):
    """
    Get team data from API and map auction prices
    Parameters
    ----------
    team_id_to_price: dict
        output of get_team_auction()

    Returns
    -------
    pandas DataFrame of all NBA teams
    """
    teams_json = requests.get(TEAMS_URL).json()["data"]
    teams_df = pd.DataFrame(teams_json).set_index("id", drop=False)
    teams_df["auction_price"] = teams_df["id"].astype(str).map(team_id_to_price)

    return teams_df


def build_leaderboard_df(game_data_df):
    """
    Build leaderboard dataframe of each owner and total number of wins/losses

    Parameters
    ----------
    game_data_df: pandas DataFrame
        output of get_game_data()

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
    return leaderboard_df.sort_values(by=["wins", "losses"], ascending=[False, True])


def build_team_breakdown_df(
    game_data_df, teams_df, team_id_to_owner, team_id_to_price, leaderboard_df
):
    """
    Build dataframe showing W-L records for each team, grouped by owner

    Parameters
    ----------
    game_data_df: pandas DataFrame
        output of get_game_data()
    teams_df: pandas DataFrame
        output of get_team_data()
    team_id_to_owner: dict
        output of get_team_owner()
    team_id_to_price: dict
        output of get_team_auction()
    leaderboard_df: pandas DataFrame
        output of build_leaderboard_df()

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
    team_breakdown_df["owner"] = team_breakdown_df["id"].astype(str).map(team_id_to_owner)
    team_breakdown_df["auction_price"] = team_breakdown_df["id"].astype(str).map(team_id_to_price)

    team_breakdown_df = team_breakdown_df.drop(columns="id")[
        ["owner", "full_name", "wins", "losses", "auction_price"]
    ]

    team_breakdown_df = team_breakdown_df.sort_values(
        by=["wins", "losses", "auction_price"], ascending=[False, True, False]
    )
    team_breakdown_df = team_breakdown_df.set_index("owner")

    return team_breakdown_df.loc[leaderboard_df.index]


def build_race_plot_df(game_data_df, leaderboard_df):
    """
    Generate dataframe showing cumulative wins per owner by date

    Parameters
    ----------
    game_data_df: pandas DataFrame
        output of get_game_data()
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


def main():
    """
    Pull data from API and generate leaderboard, team breakdown, and race plot dataframes
    """
    team_id_to_owner = get_team_owner()
    team_id_to_price = get_team_auction()

    teams_df = get_team_data(team_id_to_price)
    game_data_df = get_game_data(team_id_to_owner)

    leaderboard_df = build_leaderboard_df(game_data_df)
    team_breakdown_df = build_team_breakdown_df(
        game_data_df, teams_df, team_id_to_owner, team_id_to_price, leaderboard_df
    )
    race_plot_df = build_race_plot_df(game_data_df, leaderboard_df)

    return leaderboard_df, team_breakdown_df, race_plot_df


if __name__ == "__main__":

    print(get_game_data(get_team_owner()))

    leaderboard_df, team_breakdown_df, race_plot_df = main()
    print(leaderboard_df)
    print(team_breakdown_df)
    print(race_plot_df)
