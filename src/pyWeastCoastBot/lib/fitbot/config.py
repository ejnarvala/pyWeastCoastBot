from pyWeastCoastBot.config import GOOGLE_HEALTH_CLIENT_ID, GOOGLE_HEALTH_CLIENT_SECRET


class FitbotConfig:
    client_id = GOOGLE_HEALTH_CLIENT_ID
    client_secret = GOOGLE_HEALTH_CLIENT_SECRET
    redirect_uri = "https://ejnarvala.github.io/pyWeastCoastBot/oauth-callback.html"
    provider = "google_health"
    legacy_provider = "fitbot"
    activity_scope = "https://www.googleapis.com/auth/googlehealth.activity_and_fitness.readonly"
    scope = (activity_scope,)
