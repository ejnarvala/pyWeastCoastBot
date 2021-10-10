from settings import FITBIT_CLIENT_ID, FITBIT_CLIENT_SECRET


class FitbotConfig:

    client_id = FITBIT_CLIENT_ID
    client_secret = FITBIT_CLIENT_SECRET
    redirect_uri = "http://localhost/callback"
    provider = 'fitbot'
    scope = [
        "activity",
        "nutrition",
        "heartrate",
        "location",
        "profile",
        "settings",
        "sleep",
        "social",
    ]
