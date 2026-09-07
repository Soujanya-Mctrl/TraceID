"""
Main Entrypoint for the Face Identification & Blockchain Verification Pipeline.
Located in src/main.py.

Usage:
    # Run using Python's package syntax:
    python -m src samples/sample_faces/sample_person.jpg
    python -m src --camera
    python -m src --demo-tamper
    python -m src --server

    # Or run the script directly:
    python src/main.py samples/sample_faces/sample_person.jpg
    python src/main.py --server
"""

import argparse
import os
import sys
from dotenv import load_dotenv

# Ensure project root is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

load_dotenv(os.path.join(ROOT_DIR, ".env"))

# Suppress benign Python 3.13 lz4/BufferedReader destructor warnings on Windows
def _quiet_unraisablehook(unraisable):
    if unraisable.exc_type is ValueError and "closed file" in str(unraisable.exc_value):
        return
    if "lz4" in str(unraisable.err_msg or ""):
        return
    sys.__unraisablehook__(unraisable)

sys.unraisablehook = _quiet_unraisablehook


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa 2026: Face Identification & Blockchain Verification System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "image_path",
        type=str,
        nargs="?",
        default=None,
        help="Path to input face image (optional if using --camera or --server).",
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
        help="Demonstrate on-chain tamper detection with forged metadata payload.",
    )
    parser.add_argument(
        "--server",
        "--web",
        dest="start_server",
        action="store_true",
        help="Launch the FastAPI web server with embedded React frontend (default: http://localhost:8000).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the web server on (default: 8000).",
    )
    parser.add_argument(
        "--serp",
        type=str,
        nargs="?",
        const="__default__",
        default=None,
        help="Run standalone SerpAPI reverse-image search on the specified image.",
    )

    args = parser.parse_args()

    # Mode 1: Web Server
    if args.start_server:
        import uvicorn
        print("=" * 70)
        print(f"Starting FaceScan Web Application on http://localhost:{args.port}")
        print("=" * 70)
        uvicorn.run("web.server.server:app", host="0.0.0.0", port=args.port, reload=True)
        return

    # Mode 2: Standalone SerpAPI Search
    if args.serp is not None:
        import json
        from src.web_search.serp_search import reverse_image_search
        target_img = args.image_path if args.serp == "__default__" else args.serp
        if not target_img or target_img == "__default__":
            target_img = "samples/sample_faces/sample_person.jpg"
        print(f"Running standalone SerpAPI reverse image search on {target_img}...")
        results = reverse_image_search(target_img)
        print(json.dumps(results, indent=2, default=str))
        return

    # Mode 3: Live Camera or File Pipeline
    from src.pipeline.orchestrator import run
    if args.use_camera:
        run(use_camera=True, demo_tamper=args.demo_tamper)
    else:
        img_path = args.image_path or "samples/sample_faces/sample_person.jpg"
        run(image_path=img_path, use_camera=False, demo_tamper=args.demo_tamper)


if __name__ == "__main__":
    main()
