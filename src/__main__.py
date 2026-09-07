"""
Package execution entrypoint for src.
Allows running the pipeline with:
    python -m src [image_path] [options]
"""

import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

from .main import main

if __name__ == "__main__":
    main()

