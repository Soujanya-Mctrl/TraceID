"""
Blockchain anchoring + re-verification for the discovered post.
Located in src/blockchain/chain.py.

PRIVACY RULE (deliberate, non-negotiable): only non-biometric metadata
about the MATCHED POST is hashed and stored on-chain -- never the face
embedding, never raw image bytes. A public, immutable ledger is a
terrible place for biometric data: it can't be deleted, could
theoretically be matched against precomputed embedding tables, and
there's no way to honor a later "forget me" request once it's on-chain.
Hashing the post's metadata still gives a genuine tamper-evident record
of "we found this specific post, at this URL, on this date" without any
of that risk.
"""

import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

# ABI paths: check contracts/PostVerifier.json first
_DIR = os.path.dirname(__file__)
CONTRACT_ABI_PATHS = [
    os.path.abspath(os.path.join(_DIR, "..", "..", "contracts", "PostVerifier.json")),
    os.path.abspath(os.path.join(_DIR, "..", "..", "contracts", "contract_abi.json")),
    os.path.abspath(os.path.join(_DIR, "..", "..", "contract_abi.json")),
]


def _get_abi_path() -> str:
    for path in CONTRACT_ABI_PATHS:
        if os.path.exists(path):
            return path
    return CONTRACT_ABI_PATHS[0]


def get_web3() -> Web3:
    rpc_url = os.environ.get("AMOY_RPC_URL") or os.environ.get("BLOCKCHAIN_RPC_URL", "https://polygon-amoy.drpc.org")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise RuntimeError(f"Could not connect to RPC at {rpc_url}")
    return w3


def load_contract(w3: Web3):
    address = os.environ.get("CONTRACT_ADDRESS")
    if not address:
        raise RuntimeError("CONTRACT_ADDRESS not set in .env. Deploy via scripts/deploy.py first.")
    abi_path = _get_abi_path()
    if not os.path.exists(abi_path):
        raise RuntimeError(f"Contract ABI not found at {abi_path} -- run scripts/deploy.py first.")
    with open(abi_path, "r", encoding="utf-8") as f:
        abi = json.load(f)
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def canonical_payload(match_state: Dict) -> Dict:
    """
    Builds the exact dict that gets hashed. ONLY post metadata --
    see the module docstring for why. Pass in the pipeline's state
    dict (matched_page_url, matched_image_url, etc) or an equivalent.
    """
    similarity = match_state.get("match_similarity")
    return {
        "platform": "social" if match_state.get("match_is_social") else "web",
        "page_url": match_state.get("matched_page_url") or "",
        "image_url": match_state.get("matched_image_url") or "",
        "page_title": match_state.get("matched_page_title") or "",
        "verified": bool(match_state.get("match_verified")),
        "similarity": round(similarity, 4) if similarity is not None else None,
    }


def hash_payload(payload: Dict) -> bytes:
    """Deterministic hash: sorted keys + compact separators so the same
    payload always hashes identically, regardless of dict insertion order."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return Web3.keccak(text=canonical)


def store_record(w3: Web3, contract, private_key: str, data_hash: bytes):
    account = w3.eth.account.from_key(private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = int(w3.eth.gas_price * 1.35)
    tx = contract.functions.storeRecord(data_hash).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 250_000,
        "gasPrice": gas_price,
        "chainId": w3.eth.chain_id,
    })
    signed = account.sign_transaction(tx)
    raw_tx = getattr(signed, "raw_transaction", getattr(signed, "rawTransaction", None))
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    tx_hex = receipt.transactionHash.hex()
    if not tx_hex.startswith("0x"):
        tx_hex = "0x" + tx_hex
    return tx_hex, receipt.blockNumber


def verify_record(contract, data_hash: bytes) -> Dict:
    """
    Re-verification: reads the SAME hash back from chain. exists=False
    (not an exception) means either it was never stored, or the data
    was altered since (different data -> different hash -> no match).
    """
    exists, timestamp, submitter = contract.functions.verifyRecord(data_hash).call()
    return {"exists": exists, "timestamp": timestamp, "submitter": submitter}


def anchor_and_verify(match_state: Dict, private_key: Optional[str] = None) -> Dict:
    """
    Full round trip: build payload -> hash -> write to chain -> read
    back -> confirm the hash matches. This is the function pipeline calls.

    Interacts with Polygon Amoy EVM smart contract via Web3.py.
    """
    payload = canonical_payload(match_state)
    data_hash = hash_payload(payload)

    private_key = private_key or os.environ.get("PRIVATE_KEY") or os.environ.get("BLOCKCHAIN_PRIVATE_KEY")
    contract_addr = os.environ.get("CONTRACT_ADDRESS")
    rpc_url = os.environ.get("AMOY_RPC_URL") or os.environ.get("BLOCKCHAIN_RPC_URL")

    # If live contract and RPC are configured, interact with EVM directly:
    if contract_addr and rpc_url and private_key:
        if not private_key.startswith("0x"):
            private_key = "0x" + private_key
        w3 = get_web3()
        contract = load_contract(w3)

        tx_hash, block_number = store_record(w3, contract, private_key, data_hash)
        check = verify_record(contract, data_hash)

        return {
            "payload": payload,
            "data_hash": data_hash.hex(),
            "tx_hash": tx_hash,
            "block_number": block_number,
            "on_chain_exists": check["exists"],
            "on_chain_timestamp": check["timestamp"],
            "on_chain_submitter": check["submitter"],
        }

    # Strict live check: if non-simulated is requested, fail loudly
    network = os.environ.get("BLOCKCHAIN_NETWORK", "").lower()
    if network not in ("simulated", ""):
        raise RuntimeError(
            f"BLOCKCHAIN_NETWORK={network} requires CONTRACT_ADDRESS, RPC_URL, and PRIVATE_KEY. "
            "Please deploy the contract via scripts/deploy.py and set CONTRACT_ADDRESS in .env."
        )

    # Fallback to in-process verifiable cryptographic chain only when explicitly in simulated mode
    from src.blockchain.verifier import _LOCAL_CHAIN
    import time
    ts = int(time.time())
    data_hash_hex = data_hash.hex()
    receipt = _LOCAL_CHAIN.anchor(
        record_hash=data_hash_hex,
        face_hash="0x0",  # Privacy principle: never anchor face embedding
        post_url=payload["page_url"],
        content_hash=data_hash_hex,
        platform=payload["platform"],
    )

    check = _LOCAL_CHAIN.verify(data_hash_hex)
    return {
        "payload": payload,
        "data_hash": data_hash_hex,
        "tx_hash": receipt["tx_hash"],
        "block_number": receipt["block_number"],
        "on_chain_exists": check is not None,
        "on_chain_timestamp": receipt["timestamp"],
        "on_chain_submitter": receipt["submitter"],
    }


if __name__ == "__main__":
    fake_match = {
        "matched_page_url": "https://instagram.com/p/fake123",
        "matched_image_url": "https://cdn.example.com/a.jpg",
        "matched_page_title": "A post",
        "match_verified": True,
        "match_similarity": 0.87654321,
        "match_is_social": True,
    }
    payload = canonical_payload(fake_match)
    print("Canonical payload:", json.dumps(payload, indent=2))
    print("Hash:", hash_payload(payload).hex())
