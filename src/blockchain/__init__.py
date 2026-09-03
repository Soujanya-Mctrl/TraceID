"""Segment 3: Blockchain Verification & Cryptographic Anchoring."""

from .verifier import (
    anchor_post_record,
    reverify_against_chain,
    compute_face_hash,
    compute_record_hash,
    LocalVerifiableChain,
)

__all__ = [
    "anchor_post_record",
    "reverify_against_chain",
    "compute_face_hash",
    "compute_record_hash",
    "LocalVerifiableChain",
]
