"""Segment 2: Web & Social Media Visual Search with Face Verification."""

from .searcher import (
    find_and_verify_match,
    verify_candidate,
    reverse_image_search,
    search_web_for_face,
    extract_post_metadata,
    compute_content_fingerprint,
    detect_platform,
    VERIFY_SIMILARITY_THRESHOLD,
)
from .entity_resolver import (
    resolve_wikipedia_entity,
    clean_canonical_social_profile,
    classify_candidate_url,
)
from . import serp_search

__all__ = [
    "find_and_verify_match",
    "verify_candidate",
    "reverse_image_search",
    "search_web_for_face",
    "extract_post_metadata",
    "compute_content_fingerprint",
    "detect_platform",
    "VERIFY_SIMILARITY_THRESHOLD",
    "resolve_wikipedia_entity",
    "clean_canonical_social_profile",
    "classify_candidate_url",
    "serp_search",
]

