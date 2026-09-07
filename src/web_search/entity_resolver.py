"""
Entity Resolution & Canonical Profile Resolver.

Analyses search signals (SerpAPI Google Lens related queries, knowledge graphs,
best-guess labels) to identify public figures / individuals and resolve their
canonical identity pages (Wikipedia, official social profiles, IMDb) rather than
returning ephemeral short-form video clips or random meme reels.
"""

import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional
import requests

logger = logging.getLogger(__name__)

USER_AGENT = "FaceVerificationEngine/2.0 (Identity Canonical Resolver)"
WIKI_SUMMARY_ENDPOINT = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Domains and paths representing ephemeral/short-form content or meme reposts
EPHEMERAL_PATTERNS = [
    r"instagram\.com/reel/",
    r"instagram\.com/reels/",
    r"instagram\.com/p/",
    r"youtube\.com/shorts/",
    r"tiktok\.com/@.+/video/",
    r"pinterest\.[a-z.]+/pin/",
    r"pinterest\.[a-z.]+/ideas/",
    r"funny-short-clips",
    r"reddit\.com/r/memes",
    r"reddit\.com/r/dankmemes",
]

# Domains that represent authoritative identity records
CANONICAL_PROFILE_PATTERNS = [
    r"wikipedia\.org/wiki/",
    r"imdb\.com/name/",
    r"linkedin\.com/in/",
    r"britannica\.com/biography/",
    r"forbes\.com/profile/",
]


def resolve_wikipedia_entity(entity_name: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
    """
    Queries the Wikipedia REST API for a candidate entity/celebrity name.
    Resolves redirects (e.g. 'Ajey Nagar' -> 'CarryMinati') and returns canonical
    page URL, high-quality portrait image URL, and biographical summary.
    """
    if not entity_name or len(entity_name.strip()) < 2:
        return None

    clean_name = entity_name.strip()
    encoded = urllib.parse.quote(clean_name.replace(" ", "_"))
    url = f"{WIKI_SUMMARY_ENDPOINT}{encoded}"

    try:
        resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=timeout)
        if resp.status_code == 200:
            data = resp.json()
            page_type = data.get("type", "")
            # Skip disambiguation pages
            if page_type == "disambiguation":
                return None

            title = data.get("title")
            page_url = data.get("content_urls", {}).get("desktop", {}).get("page")
            thumbnail = data.get("thumbnail", {}).get("source")
            description = data.get("description", "")
            extract = data.get("extract", "")

            if page_url and title:
                return {
                    "entity_name": title,
                    "canonical_url": page_url,
                    "image_url": thumbnail,
                    "description": description,
                    "extract": extract,
                    "source": "Wikipedia",
                }
    except Exception as e:
        logger.debug("Wikipedia entity lookup failed for '%s': %s", entity_name, e)

    return None


def clean_canonical_social_profile(url: str, author_handle: Optional[str] = None) -> Optional[str]:
    """
    Extracts a canonical profile root link from post/reel links if an author handle is known.
    e.g. 'https://www.instagram.com/reel/xyz/' with author '@carryminati' -> 'https://www.instagram.com/carryminati/'
    """
    if not url:
        return None

    # Handle Instagram author
    if "instagram.com" in url.lower():
        if author_handle and author_handle.startswith("@"):
            handle = author_handle.lstrip("@").strip()
            if handle:
                return f"https://www.instagram.com/{handle}/"
        # Check URL path: instagram.com/<username>/p/...
        m = re.search(r"instagram\.com/([a-zA-Z0-9._]+)/(?:p|reel)/", url)
        if m:
            return f"https://www.instagram.com/{m.group(1)}/"

    # Handle Twitter / X author
    if "twitter.com" in url.lower() or "x.com" in url.lower():
        if author_handle and author_handle.startswith("@"):
            handle = author_handle.lstrip("@").strip()
            if handle:
                return f"https://x.com/{handle}"
        m = re.search(r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)/status/", url)
        if m:
            return f"https://x.com/{m.group(1)}"

    return None


def classify_candidate_url(url: Optional[str], page_title: Optional[str] = "") -> Dict[str, Any]:
    """
    Classifies candidate URLs to penalize ephemeral reels/pins and boost canonical identity profiles.
    Returns:
      - is_ephemeral_clip: bool
      - is_canonical_profile: bool
      - is_editorial: bool
      - authority_score: float (-50.0 to +50.0)
    """
    if not url:
        return {
            "is_ephemeral_clip": False,
            "is_canonical_profile": False,
            "is_editorial": False,
            "authority_score": 0.0,
        }

    url_lower = url.lower()
    title_lower = (page_title or "").lower()

    # 1. Ephemeral clip / random reel check
    for pattern in EPHEMERAL_PATTERNS:
        if re.search(pattern, url_lower):
            return {
                "is_ephemeral_clip": True,
                "is_canonical_profile": False,
                "is_editorial": False,
                "authority_score": -50.0,  # heavy penalty
            }

    # Also check title indicators for meme/short clip boards
    if any(k in title_lower for k in ["funny short clips", "meme", "short humor", "funny clips"]):
        return {
            "is_ephemeral_clip": True,
            "is_canonical_profile": False,
            "is_editorial": False,
            "authority_score": -45.0,
        }

    # 2. Authoritative identity profile check
    for pattern in CANONICAL_PROFILE_PATTERNS:
        if re.search(pattern, url_lower):
            return {
                "is_ephemeral_clip": False,
                "is_canonical_profile": True,
                "is_editorial": False,
                "authority_score": 50.0,  # top priority boost
            }

    # Clean profile roots on social platforms (e.g. linkedin.com/in/user, x.com/user without /status/)
    is_social_root = (
        bool(re.match(r"https?://(?:www\.)?x\.com/[a-zA-Z0-9_]+/?$", url_lower))
        or bool(re.match(r"https?://(?:www\.)?twitter\.com/[a-zA-Z0-9_]+/?$", url_lower))
        or bool(re.match(r"https?://(?:www\.)?instagram\.com/[a-zA-Z0-9._]+/?$", url_lower))
        or bool(re.match(r"https?://(?:www\.)?youtube\.com/@[a-zA-Z0-9._-]+/?$", url_lower))
    )
    if is_social_root:
        return {
            "is_ephemeral_clip": False,
            "is_canonical_profile": True,
            "is_editorial": False,
            "authority_score": 35.0,
        }

    # 3. High-quality editorial / feature article check
    editorial_keywords = ["magazine", "news", "article", "feature", "interview", "biography", "profile"]
    if any(k in url_lower or k in title_lower for k in editorial_keywords):
        return {
            "is_ephemeral_clip": False,
            "is_canonical_profile": False,
            "is_editorial": True,
            "authority_score": 20.0,
        }

    return {
        "is_ephemeral_clip": False,
        "is_canonical_profile": False,
        "is_editorial": False,
        "authority_score": 5.0,
    }
