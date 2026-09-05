"""
SerpAPI (Google Lens) reverse-image search backend.

Drop-in alternative to web_search.reverse_image_search -- returns the
SAME candidate schema, so it plugs into the same verify_candidate() /
find_and_verify_match() logic without any changes there.

Correct setup for LOCAL images (face crops, webcam captures), which is
what this pipeline always has -- NOT a public URL:

  1. Upload the local file via SerpApi's Image API -> get an image_id
     (valid 10 minutes, 500KB max per file, JPG/PNG/WebP only).
  2. Call the Google Lens engine with that image_id (NOT `url=`, which
     requires an already-public image and silently misbehaves on a
     local path).
  3. Use type=all in a single call to get both exact and visual matches
     for one search credit, instead of two separate calls.
"""

import logging
import os
import tempfile
from typing import Dict, List, Optional
from PIL import Image
import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

IMAGE_UPLOAD_ENDPOINT = "https://serpapi.com/image"
SEARCH_ENDPOINT = "https://serpapi.com/search"
MAX_UPLOAD_BYTES = 500 * 1024  # SerpApi's 500KB hard limit

SOCIAL_DOMAINS = [
    "linkedin.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "reddit.com",
    "github.com",
]


def _is_social_url(url: Optional[str]) -> bool:
    if not url:
        return False
    return any(domain in url.lower() for domain in SOCIAL_DOMAINS)


def _ensure_under_500kb(image_path: str) -> str:
    """
    Checks if image is under 500KB. If it exceeds 500KB (e.g. full-resolution webcam
    frames), automatically compresses/resizes it to a temporary file under 500KB.
    Returns the path to the uploadable image (original or compressed temp).
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    size = os.path.getsize(image_path)
    if size <= MAX_UPLOAD_BYTES:
        return image_path

    logger.info(
        "Image %s is %.1f KB (exceeds 500KB SerpApi limit). Auto-compressing...",
        image_path,
        size / 1024,
    )

    try:
        img = Image.open(image_path)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if very large dimension
        max_dim = 1024
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

        fd, temp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)

        # Iteratively find quality under 500KB
        for quality in (85, 75, 60, 45):
            img.save(temp_path, format="JPEG", quality=quality, optimize=True)
            if os.path.getsize(temp_path) <= MAX_UPLOAD_BYTES:
                return temp_path

        if os.path.getsize(temp_path) <= MAX_UPLOAD_BYTES:
            return temp_path
        raise RuntimeError(
            f"{image_path} exceeds 500KB limit ({size / 1024:.0f}KB) and could not be compressed below 500KB."
        )
    except Exception as e:
        raise RuntimeError(
            f"{image_path} is {size / 1024:.0f}KB, over SerpApi's 500KB upload limit: {e}"
        )


def _check_size(image_path: str):
    """Explicit size check to notify caller if original file exceeds 500KB limit."""
    size = os.path.getsize(image_path)
    if size > MAX_UPLOAD_BYTES:
        raise RuntimeError(
            f"{image_path} is {size / 1024:.0f}KB, over SerpApi's 500KB upload limit. "
            f"Resize/compress before uploading (face crops are usually fine; "
            f"full webcam captures often aren't)."
        )


def upload_image(image_path: str, api_key: Optional[str] = None) -> str:
    """
    Uploads a local image to SerpApi's Image Upload API, returns an image_id
    valid for 10 minutes.
    """
    api_key = api_key or os.environ.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set SERPAPI_API_KEY (or SERPAPI_KEY) env var or pass api_key=."
        )
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    # Compress if oversized (e.g. full-frame webcam capture)
    upload_path = _ensure_under_500kb(image_path)
    is_temp = upload_path != image_path

    try:
        with open(upload_path, "rb") as f:
            resp = requests.post(
                IMAGE_UPLOAD_ENDPOINT,
                files={"image": f},
                data={"api_key": api_key},
                timeout=20,
            )
        if resp.status_code != 200:
            raise RuntimeError(f"SerpApi image upload failed {resp.status_code}: {resp.text}")

        data = resp.json()
        image_id = data.get("image_id")
        if not image_id:
            raise RuntimeError(f"SerpApi image upload returned no image_id: {data}")
        return image_id
    finally:
        if is_temp and os.path.exists(upload_path):
            try:
                os.remove(upload_path)
            except Exception:
                pass


def reverse_image_search(image_path: str, api_key: Optional[str] = None) -> Dict:
    """
    Same return schema as web_search.reverse_image_search:
      {
        "candidates": [
          {"page_url", "image_url", "page_title", "is_social", "match_type"},
          ...
        ],
        "best_guess_labels": [str, ...],
      }
    """
    api_key = api_key or os.environ.get("SERPAPI_API_KEY") or os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set SERPAPI_API_KEY (or SERPAPI_KEY) env var or pass api_key=."
        )

    image_id = upload_image(image_path, api_key=api_key)

    params = {
        "engine": "google_lens",
        "image_id": image_id,
        "type": "all",  # one call, one credit -- gets exact + visual matches together
        "api_key": api_key,
    }
    resp = requests.get(SEARCH_ENDPOINT, params=params, timeout=30)
    if resp.status_code != 200:
        raise RuntimeError(f"SerpApi search failed {resp.status_code}: {resp.text}")

    data = resp.json()
    if data.get("search_metadata", {}).get("status") == "Error":
        raise RuntimeError(f"SerpApi search error: {data.get('error', data)}")

    candidates = []

    # "exact_matches" -- near-duplicate images, highest confidence this
    # is literally the same posted photo.
    for m in data.get("exact_matches", []):
        link = m.get("link", "")
        candidates.append({
            "page_url": link,
            "image_url": m.get("image") or m.get("thumbnail"),
            "page_title": m.get("title", ""),
            "is_social": _is_social_url(link),
            "match_type": "exact_match",
        })

    # "visual_matches" -- broader net, same as Vision's visuallySimilarImages.
    for m in data.get("visual_matches", []):
        link = m.get("link", "")
        candidates.append({
            "page_url": link,
            "image_url": m.get("image") or m.get("thumbnail"),
            "page_title": m.get("title", ""),
            "is_social": _is_social_url(link),
            "match_type": "visually_similar",
        })

    best_guess = []
    if "knowledge_graph" in data and data["knowledge_graph"].get("title"):
        best_guess.append(data["knowledge_graph"]["title"])

    return {"candidates": candidates, "best_guess_labels": best_guess}


if __name__ == "__main__":
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python serp_search.py <image_path>")
        sys.exit(1)

    results = reverse_image_search(sys.argv[1])
    print(json.dumps(results, indent=2, default=str))
