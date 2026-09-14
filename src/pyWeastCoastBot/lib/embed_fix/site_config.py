"""Declarative manifest of social-media embed fixers.

Each site has a dedicated proxy that re-serves its content with working embed
tags, so fixing a link is a plain host replacement, e.g.
``twitter.com/user/status/1`` -> ``fxtwitter.com/user/status/1``.

Domains are drawn from FixTweetBot (https://github.com/Kyrela/FixTweetBot,
`src/websites.py`). `SITES` below is the single source of truth: to add a site,
tweak a proxy domain, or drop one, edit this list — nothing else needs to change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Site:
    id: str
    label: str
    domains: tuple[str, ...]  # source domains matched (subdomains handled by matcher)
    fix_domain: str  # replacement host
    # Query params to strip as tracking. Denylist, not allowlist: everything else
    # is kept, so essential params (youtube ?v=, pixiv ?illust_id=) survive. These
    # are on top of the always-stripped set in fixer.py (utm_*, fbclid, ...).
    strip_params: tuple[str, ...] = ()


# Order matters only for reporting; matching is unambiguous by domain.
SITES: tuple[Site, ...] = (
    Site(
        "twitter",
        "Twitter / X",
        (
            "twitter.com",
            "x.com",
            "nitter.net",
            "xcancel.com",
            "nitter.poast.org",
            "nitter.privacyredirect.com",
            "lightbrd.com",
            "nitter.space",
            "nitter.tiekoetter.com",
        ),
        fix_domain="fxtwitter.com",
        strip_params=("s", "t"),
    ),
    Site("instagram", "Instagram", ("instagram.com",), fix_domain="oginstagram.com", strip_params=("igshid", "igsh")),
    Site(
        "tiktok",
        "TikTok",
        ("tiktok.com",),
        fix_domain="tnktok.com",
        strip_params=("is_from_webapp", "sender_device", "sender_web_id", "web_id", "_r", "_t"),
    ),
    Site("reddit", "Reddit", ("reddit.com", "redditmedia.com"), fix_domain="vxreddit.com", strip_params=("share_id",)),
    Site("threads", "Threads", ("threads.net", "threads.com"), fix_domain="drhong.ddns.net:9813"),
    Site("bluesky", "Bluesky", ("bsky.app",), fix_domain="fxbsky.app"),
    Site("facebook", "Facebook", ("facebook.com",), fix_domain="facebed.seria.moe"),
    Site("pixiv", "Pixiv", ("pixiv.net",), fix_domain="phixiv.net"),
    Site("twitch", "Twitch", ("twitch.tv",), fix_domain="fxtwitch.seria.moe"),
    Site("spotify", "Spotify", ("spotify.com",), fix_domain="fxspotify.com", strip_params=("si",)),
    Site(
        "mastodon",
        "Mastodon",
        (
            "mastodon.social",
            "mstdn.jp",
            "mastodon.cloud",
            "mstdn.social",
            "mastodon.world",
            "mastodon.online",
            "mas.to",
            "techhub.social",
            "mastodon.uno",
            "infosec.exchange",
        ),
        fix_domain="fxmas.to",
    ),
    Site("tumblr", "Tumblr", ("tumblr.com",), fix_domain="tpmblr.com"),
    Site(
        "youtube",
        "YouTube",
        ("youtube.com", "youtu.be"),
        fix_domain="koutube.com",
        strip_params=("si", "feature", "pp", "ab_channel"),  # keep v, t, list, index
    ),
)
