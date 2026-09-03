"""Integration tests for Segment 4: LangGraph Pipeline."""

from pathlib import Path
from src.pipeline import build_graph

SAMPLE_IMAGE = Path(__file__).resolve().parent.parent / "samples" / "sample_faces" / "sample_person.jpg"


def test_langgraph_pipeline_run():
    app = build_graph().compile()
    result = app.invoke({"image_path": str(SAMPLE_IMAGE)})

    assert result.get("error") is None
    assert result.get("matched_url") is not None
    assert result.get("tx_hash") is not None
    assert result.get("record_hash") is not None
    assert result.get("is_verified") is True
