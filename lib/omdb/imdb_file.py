import attr


@attr.s
class ImdbFilm(object):

    title = attr.ib()
    released = attr.ib()
    genre = attr.ib()
    director = attr.ib()
    actors = attr.ib()
    writer = attr.ib()
    runtime = attr.ib()
    imdb_id = attr.ib()
    rating = attr.ib()
    plot = attr.ib()
    image_url = attr.ib()

    @property
    def imdb_url(self):
        return f"https://www.imdb.com/title/{self.imdb_id}"

    @staticmethod
    def from_json(json_resp):
        return ImdbFilm(
            title=json_resp["Title"],
            released=json_resp["Released"],
            genre=json_resp["Genre"],
            director=json_resp["Director"],
            actors=json_resp["Actors"],
            writer=json_resp["Writer"],
            runtime=json_resp["Runtime"],
            imdb_id=json_resp["imdbID"],
            rating=json_resp["imdbRating"],
            plot=json_resp["Plot"],
            image_url=json_resp["Poster"],
        )
