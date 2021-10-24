import attr


@attr.s
class NbaTeam:

    id = attr.ib()
    city = attr.ib()
    conference = attr.ib()
    full_name = attr.ib()
    name = attr.ib()
    abbreviation = attr.ib()

    def to_dict(self):
        return attr.asdict(self)
