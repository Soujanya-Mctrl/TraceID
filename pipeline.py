"""
LangGraph pipeline -- Phase 1 + Phase 2 + Phase 3 wired together.

State flows through nodes:
  face_detect -> web_search (harvest + verify) -> blockchain_verify -> END

Run this file directly to test face_detect + web_search + blockchain_verify end-to-end.
"""

from typing import TypedDict, Optional, List
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from langgraph.graph import StateGraph, END

from face_detection import best_face, crop_face
from web_search import find_and_verify_match
import web_search
import serp_search
import chain

# Pick the search backend via env var: SEARCH_BACKEND=serp (default) or vision
_BACKEND = os.environ.get("SEARCH_BACKEND", "serp").lower()
_SEARCH_FN = serp_search.reverse_image_search if _BACKEND in ("serp", "serpapi", "google_lens") else web_search.reverse_image_search


class PipelineState(TypedDict, total=False):
    image_path: str
    face_embedding: Optional[List[float]]
    face_confidence: Optional[float]
    face_crop_path: Optional[str]
    matched_page_url: Optional[str]
    matched_image_url: Optional[str]
    matched_page_title: Optional[str]
    match_verified: Optional[bool]
    match_similarity: Optional[float]
    match_is_social: Optional[bool]
    match_note: Optional[str]      # present + non-empty if unverified fallback
    tx_hash: Optional[str]
    on_chain_exists: Optional[bool]
    on_chain_timestamp: Optional[int]
    error: Optional[str]


def face_detect_node(state: PipelineState) -> PipelineState:
    try:
        print("\n[Stage 1: Face Detection] Detecting & scoring face quality...")
        face = best_face(state["image_path"], min_quality=0.55)
        os.makedirs("output", exist_ok=True)
        crop_path = crop_face(
            state["image_path"], face["facial_area"], os.path.join("output", "face_crop.jpg")
        )
        return {
            **state,
            "face_embedding": face["embedding"].tolist(),
            "face_confidence": face["confidence"],
            "face_crop_path": crop_path,
        }
    except Exception as e:
        return {**state, "error": f"face_detect failed: {e}"}


def web_search_node(state: PipelineState) -> PipelineState:
    if state.get("error"):
        return state  # skip if a prior node already failed
    try:
        backend_name = "serp" if _SEARCH_FN == serp_search.reverse_image_search else "vision"
        print(f"\n[Stage 2: Web Search] Harvesting candidates via [{backend_name.upper()}] & verifying against face embedding...")
        match = find_and_verify_match(
            image_path=state["image_path"],
            original_embedding=state["face_embedding"],
            face_crop_path=state.get("face_crop_path"),
            search_fn=_SEARCH_FN,
        )
        if match is None:
            return {**state, "error": "web_search failed: no candidates found at all"}
        return {
            **state,
            "matched_page_url": match.get("page_url"),
            "matched_image_url": match.get("image_url"),
            "matched_page_title": match.get("page_title", ""),
            "match_verified": match.get("verified", False),
            "match_similarity": match.get("similarity"),
            "match_is_social": match.get("is_social"),
            "match_note": match.get("note", ""),
        }
    except Exception as e:
        return {**state, "error": f"web_search failed: {e}"}


def blockchain_verify_node(state: PipelineState) -> PipelineState:
    if state.get("error"):
        return state
    try:
        print("\n[Stage 3: Blockchain] Anchoring post metadata hash & re-verifying...")
        result = chain.anchor_and_verify(state)
        return {
            **state,
            "tx_hash": result["tx_hash"],
            "on_chain_exists": result["on_chain_exists"],
            "on_chain_timestamp": result["on_chain_timestamp"],
        }
    except Exception as e:
        return {**state, "error": f"blockchain_verify failed: {e}"}


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)
    graph.add_node("face_detect", face_detect_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("blockchain_verify", blockchain_verify_node)
    graph.set_entry_point("face_detect")
    graph.add_edge("face_detect", "web_search")
    graph.add_edge("web_search", "blockchain_verify")
    graph.add_edge("blockchain_verify", END)
    return graph


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path>")
        sys.exit(1)

    app = build_graph().compile()
    result = app.invoke({"image_path": sys.argv[1]})

    if result.get("error"):
        print(f"\nERROR: {result['error']}")
    else:
        print("\n" + "=" * 70)
        print("PIPELINE EXECUTION SUMMARY")
        print("=" * 70)
        print(f"Face confidence:     {result.get('face_confidence')}")
        print(f"Face crop saved to:  {result.get('face_crop_path')}")
        print(f"Embedding length:    {len(result.get('face_embedding', []))}")
        print(f"Matched page:        {result.get('matched_page_url')}")
        print(f"Matched image:       {result.get('matched_image_url')}")
        print(f"Verified:            {result.get('match_verified')} (similarity={result.get('match_similarity')})")
        if result.get("match_note"):
            print(f"NOTE:                {result['match_note']}")
        print(f"On-chain tx:         {result.get('tx_hash')}")
        print(f"On-chain verified:   {result.get('on_chain_exists')} (timestamp={result.get('on_chain_timestamp')})")
        print("=" * 70)
