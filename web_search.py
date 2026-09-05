"""
Web search module CLI and entrypoint.
Delegates to src.web_search.searcher.
"""

from src.web_search.searcher import (
    find_and_verify_match,
    verify_candidate,
    reverse_image_search,
    search_web_for_face,
    extract_post_metadata,
    compute_content_fingerprint,
    detect_platform,
    VERIFY_SIMILARITY_THRESHOLD,
)

if __name__ == "__main__":
    import sys
    import json
    from src.face_detection.detector import best_face

    if len(sys.argv) < 2:
        print("Usage: python web_search.py <image_path>")
        sys.exit(1)

    face = best_face(sys.argv[1])
    match = find_and_verify_match(sys.argv[1], face["embedding"].tolist())
    if match is None:
        print("No matches found.")
    else:
        print(json.dumps(match, indent=2, default=str))
