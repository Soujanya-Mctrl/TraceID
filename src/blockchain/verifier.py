"""
Segment 3: Blockchain Verification Module.
Anchors discovered social post metadata and face biometric hash onto an immutable ledger,
and verifies records against on-chain state to provide cryptographic tamper-evidence.
"""

import hashlib
import json
import os
import sys
import time
from typing import Dict, List, Optional, Tuple


def compute_face_hash(embedding: List[float]) -> str:
    """Computes a deterministic 256-bit biometric hash from face embedding vector."""
    quantized = ",".join(f"{v:.4f}" for v in embedding).encode("utf-8")
    return "0x" + hashlib.sha256(quantized).hexdigest()


def compute_record_hash(face_hash: str, post_url: str, content_hash: str, timestamp: int) -> str:
    """Computes the canonical 32-byte composite Keccak-256 / SHA3 record hash."""
    f_clean = face_hash.lower().replace("0x", "")
    c_clean = content_hash.lower().replace("0x", "")
    canonical = f"{f_clean}:{post_url.strip()}:{c_clean}:{timestamp}"
    return "0x" + hashlib.sha3_256(canonical.encode("utf-8")).hexdigest()


class LocalVerifiableChain:
    """In-process verifiable blockchain ledger for fast, reliable offline demo & verification."""

    def __init__(self):
        self.chain = []
        self.state: Dict[str, Dict] = {}
        # Genesis block
        genesis_hash = "0x" + "0" * 64
        self.chain.append({
            "index": 0,
            "timestamp": 1700000000,
            "transactions": [],
            "previous_hash": genesis_hash,
            "block_hash": "0x" + hashlib.sha256(b"genesis").hexdigest(),
        })

    def anchor(self, record_hash: str, face_hash: str, post_url: str, content_hash: str, platform: str) -> Dict:
        """Anchors a record by mining a new cryptographic block."""
        if record_hash in self.state:
            raise ValueError(f"Record {record_hash} already exists on-chain!")

        ts = int(time.time())
        tx_hash = "0x" + hashlib.sha256(f"{record_hash}:{ts}".encode("utf-8")).hexdigest()
        submitter = "0x71C8366420A01fAA32b3691c742f5349B8E3628F"

        tx = {
            "tx_hash": tx_hash,
            "record_hash": record_hash,
            "face_hash": face_hash,
            "post_url": post_url,
            "content_hash": content_hash,
            "platform": platform,
            "submitter": submitter,
            "timestamp": ts,
        }

        block_index = len(self.chain)
        prev_hash = self.chain[-1]["block_hash"]
        block_payload = f"{block_index}:{ts}:{prev_hash}:{tx_hash}"
        block_hash = "0x" + hashlib.sha256(block_payload.encode("utf-8")).hexdigest()

        self.chain.append({
            "index": block_index,
            "timestamp": ts,
            "transactions": [tx],
            "previous_hash": prev_hash,
            "block_hash": block_hash,
        })
        self.state[record_hash] = {**tx, "block_number": block_index}

        return {
            "record_hash": record_hash,
            "tx_hash": tx_hash,
            "block_number": block_index,
            "block_hash": block_hash,
            "timestamp": ts,
            "submitter": submitter,
            "network": "simulated",
        }

    def verify(self, record_hash: str) -> Optional[Dict]:
        """Reads record directly from on-chain state."""
        return self.state.get(record_hash)


# Global singleton instance for local execution
_LOCAL_CHAIN = LocalVerifiableChain()


def anchor_post_record(
    face_embedding: List[float],
    post_url: str,
    content_fingerprint: str,
    platform: str,
    timestamp: Optional[int] = None,
) -> Dict:
    """
    Main function to anchor a discovered post record onto the blockchain.
    Returns receipt containing tx_hash, block_number, and record_hash.
    """
    ts = timestamp or int(time.time())
    face_hash = compute_face_hash(face_embedding)
    rec_hash = compute_record_hash(face_hash, post_url, content_fingerprint, ts)

    receipt = _LOCAL_CHAIN.anchor(
        record_hash=rec_hash,
        face_hash=face_hash,
        post_url=post_url,
        content_hash=content_fingerprint,
        platform=platform,
    )
    receipt["face_hash"] = face_hash
    return receipt


def reverify_against_chain(
    face_embedding: List[float],
    post_url: str,
    content_fingerprint: str,
    timestamp: int,
    record_hash: str,
) -> Tuple[bool, str]:
    """
    Demonstrates tamper-evidence by comparing candidate data against on-chain record.
    """
    on_chain = _LOCAL_CHAIN.verify(record_hash)
    if not on_chain:
        return False, "Record NOT found on blockchain."

    face_hash = compute_face_hash(face_embedding)
    candidate_hash = compute_record_hash(face_hash, post_url, content_fingerprint, timestamp)

    if candidate_hash.lower() != on_chain["record_hash"].lower():
        return False, f"TAMPER DETECTED: Candidate hash {candidate_hash} != On-chain hash {on_chain['record_hash']}"

    if on_chain["post_url"] != post_url:
        return False, "TAMPER DETECTED: Post URL was altered."

    return True, "VERIFIED: Discovered data matches immutable on-chain record exactly."


if __name__ == "__main__":
    print("Testing Blockchain Verification Module...")
    dummy_emb = [0.05] * 512
    receipt = anchor_post_record(
        face_embedding=dummy_emb,
        post_url="https://x.com/tech_leader/status/1762109472304893952",
        content_fingerprint="0x" + "c" * 64,
        platform="X (Twitter)",
    )
    print(f"Anchored Block #{receipt['block_number']} | Tx: {receipt['tx_hash']}")
    print(f"Record Hash: {receipt['record_hash']}")

    # Verification
    valid, msg = reverify_against_chain(
        face_embedding=dummy_emb,
        post_url="https://x.com/tech_leader/status/1762109472304893952",
        content_fingerprint="0x" + "c" * 64,
        timestamp=receipt["timestamp"],
        record_hash=receipt["record_hash"],
    )
    print(f"Authentic Verification: {msg}")

    # Tamper test
    tampered_valid, tamper_msg = reverify_against_chain(
        face_embedding=dummy_emb,
        post_url="https://spoofed.com/malicious",
        content_fingerprint="0x" + "c" * 64,
        timestamp=receipt["timestamp"],
        record_hash=receipt["record_hash"],
    )
    print(f"Tamper Check: {tamper_msg}")
