"""Unit tests for Segment 1: Face Detection, Quality Scoring & Encoding."""

import numpy as np
from pathlib import Path
from src.face_detection import (
    best_face,
    crop_face,
    score_face,
    MIN_BLUR,
    MAX_ROLL_DEG,
    MAX_YAW_PROXY,
    _laplacian_blur,
    _roll_degrees,
    _yaw_proxy,
)

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


def test_roll_degrees_math():
    # Level eyes
    deg_level = _roll_degrees((50, 100), (150, 100))
    assert abs(deg_level) < 0.1

    # Anatomical ordering inverted (left_eye x > right_eye x)
    deg_inverted = _roll_degrees((150, 100), (50, 100))
    assert abs(deg_inverted) < 0.1

    # 45-degree tilt
    deg_45 = _roll_degrees((50, 50), (100, 100))
    assert abs(deg_45 - 45.0) < 0.1


def test_yaw_proxy_math():
    area = {"x": 100, "y": 100, "w": 200, "h": 200}
    # Perfectly centered eyes
    yaw_centered = _yaw_proxy((150, 180), (250, 180), area)
    assert yaw_centered == 0.0

    # Off-center eyes (profile)
    yaw_off = _yaw_proxy((110, 180), (150, 180), area)
    assert yaw_off > 0.3


def test_score_face_with_quality():
    face = best_face(str(SAMPLE_IMAGE), min_quality=0.55)
    assert "quality" in face
    assert face["quality"]["quality_score"] >= 0.55
    assert face["quality"]["passed"] is True
