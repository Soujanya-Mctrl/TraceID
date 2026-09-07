"""Unit tests for Segment 3: Blockchain Verification."""

from src.blockchain import (
    compute_face_hash,
    compute_record_hash,
    anchor_post_record,
    reverify_against_chain,
)


def test_compute_hashes_deterministic():
    emb = [0.1234, 0.5678] * 256
    h1 = compute_face_hash(emb)
    h2 = compute_face_hash(emb)
    assert h1 == h2
    assert h1.startswith("0x")
    assert len(h1) == 66


def test_anchor_and_reverify_authentic_data():
    emb = [0.05] * 512
    url = "https://x.com/tech_leader/status/1762109472304893952"
    content_fp = "0x" + "a" * 64

    receipt = anchor_post_record(
        face_embedding=emb,
        post_url=url,
        content_fingerprint=content_fp,
        platform="X (Twitter)",
    )

    assert receipt["block_number"] >= 1
    assert receipt["record_hash"].startswith("0x")
    assert receipt["tx_hash"].startswith("0x")

    valid, msg = reverify_against_chain(
        face_embedding=emb,
        post_url=url,
        content_fingerprint=content_fp,
        timestamp=receipt["timestamp"],
        record_hash=receipt["record_hash"],
    )
    assert valid is True
    assert "VERIFIED" in msg


def test_tamper_detection():
    emb = [0.05] * 512
    url = "https://en.wikipedia.org/wiki/CarryMinati"
    content_fp = "0x" + "b" * 64

    receipt = anchor_post_record(
        face_embedding=emb,
        post_url=url,
        content_fingerprint=content_fp,
        platform="Wikipedia / Official",
    )

    # Forged URL parameter to test cryptographic tamper detection
    valid, msg = reverify_against_chain(
        face_embedding=emb,
        post_url=f"{url}?tamper_auth_bypass=1",
        content_fingerprint=content_fp,
        timestamp=receipt["timestamp"],
        record_hash=receipt["record_hash"],
    )
    assert valid is False
    assert "TAMPER DETECTED" in msg
