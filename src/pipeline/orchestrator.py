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
from langgraph.graph import StateGraph, END

# Import the 3 modular segments from src
from src.face_detection import best_face, crop_face
from src.web_search import search_web_for_face
from src.blockchain import anchor_post_record, reverify_against_chain


class PipelineState(TypedDict, total=False):
    image_path: Optional[str]
    use_camera: Optional[bool]
    # Segment 1: Face Detection
    face_embedding: Optional[List[float]]
    face_confidence: Optional[float]
    face_crop_path: Optional[str]
    # Segment 2: Web & Social Search
    matched_url: Optional[str]
    post_platform: Optional[str]
    post_author: Optional[str]
    content_fingerprint: Optional[str]
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
    """Node 2: Web & Social Media Visual Search."""
    if state.get("error"):
        return state

    try:
        print("\n[Stage 2: Web Search] Searching web & social platforms for matching post...")
        matches = search_web_for_face(state["face_crop_path"])
        if not matches:
            return {**state, "error": "No matching social media posts discovered."}

        top_post = matches[0]
        print(f"  Discovered Post: {top_post['url']}")
        print(f"  Platform: {top_post['platform']} | Author: {top_post['author']}")
        print(f"  Content Fingerprint: {top_post['content_fingerprint']}")

        return {
            **state,
            "matched_url": top_post["url"],
            "post_platform": top_post["platform"],
            "post_author": top_post["author"],
            "content_fingerprint": top_post["content_fingerprint"],
        }
    except Exception as e:
        return {**state, "error": f"web_search failed: {e}"}


def blockchain_verify_node(state: PipelineState) -> PipelineState:
    """Node 3: Blockchain Anchoring & Tamper-Evident Re-Verification."""
    if state.get("error"):
        return state

    try:
        print("\n[Stage 3 & 4: Blockchain] Anchoring record to blockchain and verifying...")
        receipt = anchor_post_record(
            face_embedding=state["face_embedding"],
            post_url=state["matched_url"],
            content_fingerprint=state["content_fingerprint"],
            platform=state["post_platform"],
        )
        print(f"  Anchored on Block #{receipt['block_number']}")
        print(f"  Transaction Hash: {receipt['tx_hash']}")
        print(f"  Record Hash: {receipt['record_hash']}")

        valid, msg = reverify_against_chain(
            face_embedding=state["face_embedding"],
            post_url=state["matched_url"],
            content_fingerprint=state["content_fingerprint"],
            timestamp=receipt["timestamp"],
            record_hash=receipt["record_hash"],
        )
        print(f"  Re-verification Status: {msg}")

        # Save audit receipt
        receipt_data = {
            "image_path": state["image_path"],
            "face_confidence": state["face_confidence"],
            "matched_url": state["matched_url"],
            "platform": state["post_platform"],
            "author": state["post_author"],
            "content_fingerprint": state["content_fingerprint"],
            "tx_hash": receipt["tx_hash"],
            "block_number": receipt["block_number"],
            "record_hash": receipt["record_hash"],
            "verified": valid,
            "timestamp": receipt["timestamp"],
        }
        receipt_file = os.path.join("output", "verification_receipt.json")
        with open(receipt_file, "w", encoding="utf-8") as f:
            json.dump(receipt_data, f, indent=2)
        print(f"  Persisted verification receipt to: {receipt_file}")

        return {
            **state,
            "tx_hash": receipt["tx_hash"],
            "block_number": receipt["block_number"],
            "record_hash": receipt["record_hash"],
            "blockchain_timestamp": receipt["timestamp"],
            "is_verified": valid,
            "verification_details": msg,
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
    print(f"  Matched Post URL:    {result['matched_url']}")
    print(f"  Blockchain Block:    #{result['block_number']}")
    print(f"  Transaction Hash:    {result['tx_hash']}")
    print(f"  On-Chain Verified:   {result['is_verified']}")
    print("=" * 70)

    if demo_tamper:
        print("\n[Tamper Demonstration]: Testing forged post URL against blockchain...")
        forged_url = "https://spoofed.com/malicious_post"
        tampered_valid, tamper_msg = reverify_against_chain(
            face_embedding=result["face_embedding"],
            post_url=forged_url,
            content_fingerprint=result["content_fingerprint"],
            timestamp=result["blockchain_timestamp"],
            record_hash=result["record_hash"],
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
