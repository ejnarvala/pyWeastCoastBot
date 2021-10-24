from datetime import datetime
import attr
from dateutil import parser


def format_date(data):
    if isinstance(data, datetime):
        return data
    if isinstance(data, str):
        return parser.isoparse(data)


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
