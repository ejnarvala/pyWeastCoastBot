import attr


def format_date(data):
    if not data:
        return
    return data.fromisoformat(data)


@attr.s
class NbaGame:

    id = attr.ib()
    date = attr.ib(converter=format_date)
    home_team = attr.ib()
    home_team_score = attr.ib()
    status = attr.ib()
    visitor_team = attr.ib()
    visitor_team_score = attr.ib()

    def to_dict(self):
        return attr.asdict(self)
