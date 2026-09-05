"""
LangGraph pipeline orchestrator CLI and root entrypoint.
Wires:
  face_detect -> web_search (Google Lens / Vision + Face Verification) -> blockchain_verify -> END
"""

import sys
from dotenv import load_dotenv

load_dotenv()

from src.pipeline.orchestrator import (
    PipelineState,
    build_graph,
    run,
    face_detect_node,
    web_search_node,
    blockchain_verify_node,
    _get_search_backend,
)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pipeline.py <image_path> [--demo-tamper]")
        sys.exit(1)

    image_path = sys.argv[1]
    demo_tamper = "--demo-tamper" in sys.argv
    run(image_path=image_path, use_camera=False, demo_tamper=demo_tamper)
