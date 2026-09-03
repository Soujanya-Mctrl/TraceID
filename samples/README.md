# Sample Images for Testing & Demonstration

This directory contains sample face scans for running the end-to-end pipeline:

- `sample_faces/sample_person.jpg`: Standard front-facing portrait scan used for default pipeline execution and automated tests.

You can place your own images (PNG/JPG) here or pass any image path via the `--input` flag:
```bash
python run_pipeline.py --input samples/sample_faces/your_image.jpg
```
