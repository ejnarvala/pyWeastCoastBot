from datetime import datetime

import attr

MAX_PER_PAGE = 100


def _format_date(data):
    if not data:
        return
    if not isinstance(data, datetime):
        raise TypeError
    return data.strftime("%Y-%m-%d")


def _format_list(data):
    if not data:
        return
    if not isinstance(data, list):
        raise TypeError
    return ",".join(data)


@attr.s
class BallDontLieParams:

    start_date = attr.ib(converter=_format_date, default=None)
    end_date = attr.ib(converter=_format_date, default=None)
    postseason = attr.ib(default=None)
    seasons = attr.ib(converter=_format_list, default=None)
    player_ids = attr.ib(converter=_format_list, default=None)
    game_ids = attr.ib(converter=_format_list, default=None)
    page = attr.ib(default=0)
    per_page = attr.ib(default=MAX_PER_PAGE)

    def to_dict(self):
        params = {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "seasons[]": self.seasons,
            "player_ids[]": self.player_ids,
            "game_ids[]": self.game_ids,
            "per_page": self.per_page,
        }
        return {k: v for k, v in params.items() if v}
