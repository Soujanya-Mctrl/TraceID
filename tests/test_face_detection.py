"""Unit tests for Segment 1: Face Detection & Encoding."""

from pathlib import Path
from src.face_detection import best_face, crop_face

SAMPLE_IMAGE = Path(__file__).resolve().parent.parent / "samples" / "sample_faces" / "sample_person.jpg"


def test_face_detection_returns_face():
    face = best_face(str(SAMPLE_IMAGE))
    assert face is not None
    assert face["confidence"] >= 0.70
    assert len(face["embedding"]) == 512
    assert "facial_area" in face


def test_crop_face_creates_file(tmp_path):
    face = best_face(str(SAMPLE_IMAGE))
    out_crop = tmp_path / "crop_test.jpg"
    res = crop_face(str(SAMPLE_IMAGE), face["facial_area"], str(out_crop), padding=0.3)
    assert Path(res).exists()
    assert Path(res).stat().st_size > 0


def test_camera_module_callable():
    from src.face_detection import scan_face
    assert callable(scan_face)

