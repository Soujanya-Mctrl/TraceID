"""
Entrypoint for the Face Identification & Blockchain Verification Pipeline.
Usage:
    python main.py --camera
    python main.py samples/sample_faces/sample_person.jpg
    python main.py samples/sample_faces/sample_person.jpg --demo-tamper
"""

from dotenv import load_dotenv
load_dotenv()

from src.pipeline import main

if __name__ == "__main__":
    main()
