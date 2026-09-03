"""Unit tests for Segment 2: Web & Social Media Search."""

from src.web_search import detect_platform, compute_content_fingerprint, extract_post_metadata


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
