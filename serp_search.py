"""
SerpAPI reverse-image search CLI and module entrypoint.
Delegates to src.web_search.serp_search.
"""

from src.web_search.serp_search import (
    IMAGE_UPLOAD_ENDPOINT,
    SEARCH_ENDPOINT,
    MAX_UPLOAD_BYTES,
    SOCIAL_DOMAINS,
    upload_image,
    reverse_image_search,
    _is_social_url,
    _check_size,
)

if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python serp_search.py <image_path>")
        sys.exit(1)

    results = reverse_image_search(sys.argv[1])
    print(json.dumps(results, indent=2, default=str))
