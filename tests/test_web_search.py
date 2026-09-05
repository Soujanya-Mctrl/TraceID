"""Unit tests for Segment 2: Web & Social Media Search with Verification."""

import numpy as np
from src.web_search import (
    detect_platform,
    compute_content_fingerprint,
    extract_post_metadata,
    find_and_verify_match,
    verify_candidate,
)
from src.web_search.searcher import _cosine_similarity


def test_detect_platform():
    assert detect_platform("https://x.com/user/status/123") == "X (Twitter)"
    assert detect_platform("https://twitter.com/user/status/123") == "X (Twitter)"
    assert detect_platform("https://linkedin.com/in/john") == "LinkedIn"
    assert detect_platform("https://reddit.com/r/test") == "Reddit"


def test_compute_fingerprint_deterministic():
    fp1 = compute_content_fingerprint("https://x.com/test", "@user", "content", None)
    fp2 = compute_content_fingerprint("https://x.com/test", "@user", "content", None)
    assert fp1 == fp2
    assert fp1.startswith("0x")
    assert len(fp1) == 66


def test_extract_post_metadata():
    meta = extract_post_metadata(
        url="https://x.com/tech_leader/status/1762109472304893952",
        fallback_title="Keynote portrait",
        fallback_snippet="Sharing insights live.",
    )
    assert meta["platform"] == "X (Twitter)"
    assert meta["author"] == "@tech_leader"
    assert meta["content_fingerprint"].startswith("0x")


def test_cosine_similarity_identical_and_orthogonal():
    v1 = np.random.randn(512).astype(np.float32)
    sim_self = _cosine_similarity(v1, v1)
    assert abs(sim_self - 1.0) < 1e-4

    v_orth_1 = np.array([1.0, 0.0, 0.0])
    v_orth_2 = np.array([0.0, 1.0, 0.0])
    sim_orth = _cosine_similarity(v_orth_1, v_orth_2)
    assert abs(sim_orth) < 1e-4


def test_verify_candidate_without_image_url():
    cand = {"page_url": "https://x.com/post", "image_url": None, "is_social": True}
    res = verify_candidate([0.1] * 512, cand)
    assert res["verified"] is False
    assert res["similarity"] is None
    assert "no direct image URL" in res["verify_error"]


def test_find_and_verify_match_fallback():
    dummy_embedding = [0.1] * 512
    res = find_and_verify_match(
        image_path="samples/sample_faces/sample_person.jpg",
        original_embedding=dummy_embedding,
    )
    assert res is not None
    assert "url" in res
    assert "content_fingerprint" in res
    assert res["content_fingerprint"].startswith("0x")


def test_serp_search_social_check():
    from src.web_search.serp_search import _is_social_url
    assert _is_social_url("https://www.instagram.com/p/C_12345/") is True
    assert _is_social_url("https://x.com/tech_leader/status/123") is True
    assert _is_social_url("https://randomblog.org/news/today") is False


def test_serp_search_candidate_mapping(monkeypatch):
    from src.web_search import serp_search

    # Mock upload_image to return dummy id
    monkeypatch.setattr(serp_search, "upload_image", lambda path, api_key=None: "mock_img_id_123")

    # Mock requests.get returning SerpApi Google Lens shape
    class MockResponse:
        status_code = 200
        def json(self):
            return {
                "search_metadata": {"status": "Success"},
                "exact_matches": [
                    {
                        "link": "https://instagram.com/p/exact123",
                        "title": "Exact Instagram Portrait Post",
                        "thumbnail": "https://instagram.com/pic1.jpg",
                    }
                ],
                "visual_matches": [
                    {
                        "link": "https://techblog.com/speaker-news",
                        "title": "Speaker Profile",
                        "image": "https://techblog.com/speaker.jpg",
                    }
                ],
                "knowledge_graph": {"title": "Keynote Speaker Face Scan"},
            }

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: MockResponse())

    res = serp_search.reverse_image_search("samples/sample_faces/sample_person.jpg", api_key="dummy_key")
    assert "candidates" in res
    assert len(res["candidates"]) == 2

    c1 = res["candidates"][0]
    assert c1["page_url"] == "https://instagram.com/p/exact123"
    assert c1["image_url"] == "https://instagram.com/pic1.jpg"
    assert c1["is_social"] is True
    assert c1["match_type"] == "exact_match"

    c2 = res["candidates"][1]
    assert c2["page_url"] == "https://techblog.com/speaker-news"
    assert c2["image_url"] == "https://techblog.com/speaker.jpg"
    assert c2["is_social"] is False
    assert c2["match_type"] == "visually_similar"

    assert "Keynote Speaker Face Scan" in res["best_guess_labels"]


def test_find_and_verify_match_with_injected_search_fn():
    dummy_embedding = [0.1] * 512

    def mock_search_fn(img_path, api_key=None):
        return {
            "candidates": [
                {
                    "page_url": "https://linkedin.com/in/keynote_profile",
                    "image_url": None,
                    "page_title": "Keynote Speaker LinkedIn",
                    "is_social": True,
                    "match_type": "exact_match",
                }
            ],
            "best_guess_labels": ["Speaker"],
        }

    res = find_and_verify_match(
        image_path="samples/sample_faces/sample_person.jpg",
        original_embedding=dummy_embedding,
        search_fn=mock_search_fn,
    )
    assert res is not None
    assert "linkedin.com" in res["page_url"]
    assert res["is_social"] is True

