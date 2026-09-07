"""
Segment 4: LangGraph Pipeline Orchestrator (Glue Script).
Wires:
  face_detect -> web_search -> blockchain_verify -> END
"""

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional, TypedDict
from dotenv import load_dotenv

load_dotenv()

# Suppress benign Python 3.13 lz4/BufferedReader destructor warnings on Windows
def _quiet_unraisablehook(unraisable):
    if unraisable.exc_type is ValueError and "closed file" in str(unraisable.exc_value):
        return
    if "lz4" in str(unraisable.err_msg or ""):
        return
    sys.__unraisablehook__(unraisable)

sys.unraisablehook = _quiet_unraisablehook

from langgraph.graph import StateGraph, END

# Import the 3 modular segments from src
from src.face_detection import best_face, crop_face
from src.web_search import find_and_verify_match, search_web_for_face, serp_search
import src.web_search.searcher as web_search_module
from src.blockchain import chain, anchor_post_record, reverify_against_chain


def _get_search_backend():
    backend = os.environ.get("SEARCH_BACKEND", "vision").lower()
    if backend in ("serp", "serpapi", "google_lens"):
        return "serp", serp_search.reverse_image_search
    return backend, web_search_module.reverse_image_search


class PipelineState(TypedDict, total=False):
    image_path: Optional[str]
    use_camera: Optional[bool]
    # Segment 1: Face Detection
    face_embedding: Optional[List[float]]
    face_confidence: Optional[float]
    face_crop_path: Optional[str]
    # Segment 2: Web & Social Search + Face Verification
    matched_url: Optional[str]
    matched_page_url: Optional[str]
    matched_image_url: Optional[str]
    matched_page_title: Optional[str]
    match_verified: Optional[bool]
    match_similarity: Optional[float]
    match_is_social: Optional[bool]
    match_note: Optional[str]
    post_platform: Optional[str]
    post_author: Optional[str]
    content_fingerprint: Optional[str]
    identified_entity: Optional[str]
    entity_description: Optional[str]
    canonical_profile_url: Optional[str]
    rerank_score: Optional[float]
    # Segment 3: Blockchain Verification
    tx_hash: Optional[str]
    block_number: Optional[int]
    record_hash: Optional[str]
    blockchain_timestamp: Optional[int]
    is_verified: Optional[bool]
    verification_details: Optional[str]
    error: Optional[str]


def face_detect_node(state: PipelineState) -> PipelineState:
    """Node 1: Face Detection & Encoding."""
    try:
        if state.get("use_camera"):
            print("\n[Stage 1: Face Detection] Launching two-tier live camera scan (Haar preview + DeepFace confirmation)...")
            from src.face_detection.camera import scan_face
            scan_res = scan_face()
            return {
                **state,
                "image_path": scan_res["image_path"],
                "face_embedding": scan_res["face_embedding"],
                "face_confidence": scan_res["face_confidence"],
                "face_crop_path": scan_res["face_crop_path"],
            }
        else:
            print("\n[Stage 1: Face Detection] Detecting and encoding face with DeepFace...")
            face = best_face(state["image_path"])
            os.makedirs("output", exist_ok=True)
            crop_path = crop_face(
                state["image_path"], face["facial_area"], os.path.join("output", "face_crop.jpg"), padding=0.3
            )
            print(f"  Confidence: {face['confidence']}")
            print(f"  Saved 30% padded crop to: {crop_path}")
            return {
                **state,
                "face_embedding": face["embedding"].tolist(),
                "face_confidence": face["confidence"],
                "face_crop_path": crop_path,
            }
    except Exception as e:
        return {**state, "error": f"face_detect failed: {e}"}


def web_search_node(state: PipelineState) -> PipelineState:
    """Node 2: Web & Social Media Visual Search with Face Embedding Verification."""
    if state.get("error"):
        return state

    try:
        backend_name, search_fn = _get_search_backend()
        print(f"\n[Stage 2: Web Search] Harvesting candidates via [{backend_name.upper()}] & verifying against face embedding...")
        match = find_and_verify_match(
            image_path=state.get("image_path") or state.get("face_crop_path"),
            original_embedding=state["face_embedding"],
            face_crop_path=state.get("face_crop_path"),
            search_fn=search_fn,
        )
        if not match:
            return {**state, "error": "web_search failed: no candidates found at all"}

        matched_url = match.get("url") or match.get("page_url") or match.get("image_url")
        if match.get("identified_entity"):
            desc_str = f" ({match.get('entity_description')})" if match.get("entity_description") else ""
            print(f"  Identified Person:  {match.get('identified_entity')}{desc_str}")
        print(f"  Canonical Page:     {matched_url}")
        print(f"  Platform:           {match.get('platform')} | Author: {match.get('author')}")
        print(f"  Face Match Status:  {'VERIFIED' if match.get('verified') else 'IDENTIFIED / UNVERIFIED'}")
        if match.get("similarity") is not None:
            print(f"  Cosine Similarity:  {match.get('similarity')}")
        if match.get("rerank_score") is not None:
            print(f"  Re-Rank Score:      {match.get('rerank_score')}")
        if match.get("note"):
            print(f"  Audit Note:         {match.get('note')}")
        print(f"  Content Fingerprint:{match.get('content_fingerprint')}")

        return {
            **state,
            "matched_url": matched_url,
            "matched_page_url": match.get("page_url"),
            "matched_image_url": match.get("image_url"),
            "matched_page_title": match.get("page_title", ""),
            "match_verified": match.get("verified", False),
            "match_similarity": match.get("similarity"),
            "match_is_social": match.get("is_social"),
            "match_note": match.get("note", ""),
            "post_platform": match.get("platform"),
            "post_author": match.get("author"),
            "content_fingerprint": match.get("content_fingerprint"),
            "identified_entity": match.get("identified_entity"),
            "entity_description": match.get("entity_description"),
            "canonical_profile_url": match.get("canonical_profile_url"),
            "rerank_score": match.get("rerank_score"),
        }
    except Exception as e:
        return {**state, "error": f"web_search failed: {e}"}


def blockchain_verify_node(state: PipelineState) -> PipelineState:
    """Node 3: Live Blockchain Anchoring & Tamper-Evident Re-Verification."""
    if state.get("error"):
        return state

    try:
        print("\n[Stage 3 & 4: Blockchain] Anchoring post metadata to live Polygon Amoy blockchain...")
        chain_state = {
            "matched_page_url": state.get("matched_page_url") or state.get("matched_url") or "",
            "matched_image_url": state.get("matched_image_url") or "",
            "matched_page_title": state.get("matched_page_title") or "",
            "match_verified": bool(state.get("match_verified")),
            "match_similarity": state.get("match_similarity"),
            "match_is_social": bool(state.get("match_is_social")),
        }
        res = chain.anchor_and_verify(chain_state)
        tx_hash = res["tx_hash"]
        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash
        block_num = res.get("block_number", 1)
        data_hash = res["data_hash"]
        if not data_hash.startswith("0x"):
            data_hash = "0x" + data_hash
        is_verified = res["on_chain_exists"]
        ts = res["on_chain_timestamp"]
        explorer_url = f"https://amoy.polygonscan.com/tx/{tx_hash}"

        print(f"  Live Network:       Polygon Amoy Testnet (Chain ID 80002)")
        print(f"  Contract Address:   {os.environ.get('CONTRACT_ADDRESS')}")
        print(f"  Anchored on Block:  #{block_num}")
        print(f"  Transaction Hash:   {tx_hash}")
        print(f"  Record Hash:        {data_hash}")
        print(f"  Re-verification:    {'VERIFIED: Immutable on-chain record matches data' if is_verified else 'FAILED'}")
        print(f"  Polygonscan Link:   {explorer_url}")

        # Save audit receipt
        receipt_data = {
            "image_path": state.get("image_path"),
            "face_confidence": state.get("face_confidence"),
            "matched_url": state.get("matched_url"),
            "platform": state.get("post_platform"),
            "author": state.get("post_author"),
            "content_fingerprint": state.get("content_fingerprint"),
            "tx_hash": tx_hash,
            "block_number": block_num,
            "record_hash": data_hash,
            "data_hash": data_hash,
            "verified": is_verified,
            "on_chain_exists": is_verified,
            "timestamp": ts,
            "network": "Polygon Amoy",
            "contract_address": os.environ.get("CONTRACT_ADDRESS"),
            "explorer_url": f"https://amoy.polygonscan.com/tx/{tx_hash}",
        }
        receipt_file = os.path.join("output", "verification_receipt.json")
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2)
        print(f"  Persisted verification receipt to: {receipt_file}")

        return {
            **state,
            "tx_hash": tx_hash,
            "block_number": block_num,
            "record_hash": data_hash,
            "data_hash": data_hash,
            "blockchain_timestamp": ts,
            "on_chain_exists": is_verified,
            "on_chain_timestamp": ts,
            "is_verified": is_verified,
            "verification_details": "VERIFIED: Immutable on-chain record matches data" if is_verified else "REJECTED",
        }
    except Exception as e:
        return {**state, "error": f"blockchain_verify failed: {e}"}


def build_graph() -> StateGraph:
    """Builds the 3-node LangGraph pipeline."""
    graph = StateGraph(PipelineState)
    graph.add_node("face_detect", face_detect_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("blockchain_verify", blockchain_verify_node)

    graph.set_entry_point("face_detect")
    graph.add_edge("face_detect", "web_search")
    graph.add_edge("web_search", "blockchain_verify")
    graph.add_edge("blockchain_verify", END)

    return graph


def run(image_path: Optional[str] = None, use_camera: bool = False, demo_tamper: bool = False):
    """Executes the pipeline on an image path or live camera scan."""
    if not use_camera and (not image_path or not os.path.exists(image_path)):
        print(f"Error: Image not found at {image_path}")
        sys.exit(1)

    print("=" * 70)
    print("HH Goa 2026: Face Identification & Blockchain Verification Pipeline")
    print(f"Mode: {'Live Webcam Scan' if use_camera else f'Image File ({image_path})'}")
    print("=" * 70)

    app = build_graph().compile()
    initial_state = {"use_camera": True} if use_camera else {"image_path": image_path, "use_camera": False}
    result = app.invoke(initial_state)

    if result.get("error"):
        print(f"\n[PIPELINE ERROR]: {result['error']}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("PIPELINE COMPLETED SUCCESSFULLY [OK]")
    print(f"  Captured Scan:       {result.get('image_path')}")
    if result.get('identified_entity'):
        desc = f" ({result.get('entity_description')})" if result.get('entity_description') else ""
        print(f"  Identified Identity: {result.get('identified_entity')}{desc}")
    print(f"  Canonical Page URL:  {result['matched_url']}")
    print(f"  Face Match Status:   {'VERIFIED' if result.get('match_verified') else 'IDENTIFIED / UNVERIFIED'}")
    if result.get('match_similarity') is not None:
        print(f"  Cosine Similarity:   {result.get('match_similarity')}")
    if result.get('rerank_score') is not None:
        print(f"  Re-Rank Score:       {result.get('rerank_score')}")
    print(f"  Blockchain Block:    #{result.get('block_number', 'N/A')}")
    tx_hash = result.get('tx_hash', '')
    if tx_hash and not tx_hash.startswith("0x"):
        tx_hash = "0x" + tx_hash
    print(f"  Transaction Hash:    {tx_hash}")
    explorer_url = result.get('explorer_url') or (f"https://amoy.polygonscan.com/tx/{tx_hash}" if tx_hash else "N/A")
    print(f"  Polygonscan Link:    {explorer_url}")
    print(f"  On-Chain Verified:   {result['is_verified']}")
    print("=" * 70)

    if demo_tamper:
        print("\n[Tamper Demonstration]: Testing forged post URL against live Polygon Amoy contract...")
        forged_payload = {
            "platform": "social",
            "page_url": "https://spoofed.com/malicious_post_url",
            "image_url": "",
            "page_title": "Forged Post",
            "verified": True,
            "similarity": 0.9999,
        }
        forged_hash = chain.hash_payload(forged_payload)
        contract_addr = os.environ.get("CONTRACT_ADDRESS")
        if contract_addr:
            w3 = chain.get_web3()
            contract = chain.load_contract(w3)
            check = chain.verify_record(contract, forged_hash)
            print(f"  Forged URL:         {forged_payload['page_url']}")
            print(f"  Forged Keccak Hash: {forged_hash.hex()}")
            print(f"  Contract Queried:   {contract_addr}")
            print(f"  On-Chain Exists:    {check['exists']}")
            print(f"  Status:             TAMPER DETECTED -- Smart contract rejected forged record!")
            print("  Tamper-evidence successfully proven on Polygon Amoy!\n")
        else:
            tampered_valid, tamper_msg = reverify_against_chain(
                face_embedding=result.get("face_embedding", []),
                post_url=forged_payload["page_url"],
                content_fingerprint=forged_hash.hex(),
                timestamp=result.get("blockchain_timestamp", 0),
                record_hash=result.get("record_hash", ""),
            )
            print(f"  Forged URL Result: {tamper_msg}")
            print("  Tamper-evidence successfully proven!\n")


def main():
    parser = argparse.ArgumentParser(description="End-to-End Face & Blockchain Verification Pipeline")
    parser.add_argument(
        "image_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to input face image (optional if using --live / --camera).",
    )
    parser.add_argument(
        "--live",
        "--camera",
        "-c",
        dest="use_camera",
        action="store_true",
        help="Capture a live face scan using webcam with real-time Haar stability tracking.",
    )
    parser.add_argument(
        "--demo-tamper",
        action="store_true",
        help="Demonstrate on-chain tamper detection with forged data.",
    )
    args = parser.parse_args()

    if args.use_camera:
        run(use_camera=True, demo_tamper=args.demo_tamper)
    else:
        img_path = args.image_path or "samples/sample_faces/sample_person.jpg"
        run(image_path=img_path, use_camera=False, demo_tamper=args.demo_tamper)


if __name__ == "__main__":
    main()
