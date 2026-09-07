"""
Package execution entrypoint for src.
Allows running the pipeline with:
    python -m src [image_path] [options]
"""

from .main import main

if __name__ == "__main__":
    main()
