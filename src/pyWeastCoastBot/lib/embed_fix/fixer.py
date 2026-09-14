"""Match social-media links against the manifest and rewrite them so they embed.

`match_site` locates the manifest entry for a URL; `fix_url` rewrites a single
link and `fix_links` rewrites every fixable link in a block of text. All pure and
network-free. See `site_config.py` for the list of supported sites.
"""

import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pyWeastCoastBot.lib.embed_fix.site_config import SITES, Site

# Tracking params stripped from every site, on top of each site's own list.
# `utm_*` is matched by prefix; these are matched exactly.
_GLOBAL_STRIP = frozenset({"fbclid", "gclid", "mc_cid", "mc_eid"})

# Every source domain in the manifest, longest first so alternation prefers the
# most specific match. Used to build a regex anchored on known sites.
_DOMAINS = sorted({domain for site in SITES for domain in site.domains}, key=len, reverse=True)
_DOMAIN_ALT = "|".join(re.escape(domain) for domain in _DOMAINS)

# Matches links to known sites, with or without scheme/www/subdomains, excluding
# the angle brackets Discord uses to wrap embed-suppressed links (<https://...>).
# The leading lookbehind avoids matching inside emails (bob@x.com) or words.
URL_RE = re.compile(
    r"(?<![@\w.])"
    r"(?:https?://)?"  # optional scheme
    r"(?:[a-z0-9-]+\.)*"  # optional subdomains, including www
    r"(?:" + _DOMAIN_ALT + r")"  # a known source domain
    r"(?:/[^\s<>]*)?",  # optional path/query/fragment
    re.IGNORECASE,
)

# Trailing characters that are usually punctuation/markdown, not part of the URL.
_TRAILING = ".,!?;:)]}\"'"


def _clean(url: str) -> str:
    url = url.strip().rstrip(_TRAILING)
    # Tolerate schemeless links (x.com/..., www.x.com/...); default to https.
    return url if "://" in url else "https://" + url


def _host(netloc: str) -> str:
    """Lowercased hostname with the port and a leading ``www.`` stripped."""
    host = netloc.split(":")[0].lower()
    return host[4:] if host.startswith("www.") else host


def _strip_tracking(query: str, site: Site) -> str:
    """Drop known tracking params, keeping everything else (order preserved)."""
    if not query:
        return ""
    kept = [
        (key, value)
        for key, value in parse_qsl(query, keep_blank_values=True)
        if not (key.lower().startswith("utm_") or key.lower() in _GLOBAL_STRIP or key.lower() in site.strip_params)
    ]
    return urlencode(kept)


def match_site(url: str) -> Site | None:
    """Return the manifest entry that handles this URL, or None if unsupported."""
    parts = urlsplit(_clean(url))
    # Reject userinfo (user@host) so emails are never treated as URLs; none of
    # these social links use it anyway.
    if not parts.netloc or "@" in parts.netloc:
        return None
    host = _host(parts.netloc)
    for site in SITES:
        for domain in site.domains:
            # Match the domain itself or any subdomain (old.reddit.com, vm.tiktok.com).
            if host == domain or host.endswith("." + domain):
                return site
    return None


def fix_url(url: str) -> str | None:
    """Rewrite a URL's host to its fix domain (dropping any subdomain), or None if unsupported.

    The scheme is always normalized to https, and known tracking params are removed.
    """
    site = match_site(url)
    if site is None:
        return None
    parts = urlsplit(_clean(url))
    query = _strip_tracking(parts.query, site)
    return urlunsplit(("https", site.fix_domain, parts.path, query, parts.fragment))


def fix_links(text: str) -> list[str]:
    """Find every fixable URL in a block of text and return the rewritten versions."""
    fixed = []
    for match in URL_RE.finditer(text):
        rewritten = fix_url(match.group(0))
        if rewritten:
            fixed.append(rewritten)
    return fixed
