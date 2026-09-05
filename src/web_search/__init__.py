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
    "serp_search",
]

