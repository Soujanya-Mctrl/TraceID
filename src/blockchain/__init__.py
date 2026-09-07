"""Segment 3: Blockchain Verification & Cryptographic Anchoring."""

from .verifier import (
    anchor_post_record,
    reverify_against_chain,
    compute_face_hash,
    compute_record_hash,
    LocalVerifiableChain,
)
from .chain import (
    canonical_payload,
    hash_payload,
    store_record,
    verify_record,
    anchor_and_verify,
)
from . import chain

__all__ = [
    "anchor_post_record",
    "reverify_against_chain",
    "compute_face_hash",
    "compute_record_hash",
    "LocalVerifiableChain",
    "canonical_payload",
    "hash_payload",
    "store_record",
    "verify_record",
    "anchor_and_verify",
    "chain",
]

