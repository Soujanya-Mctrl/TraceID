"""Root shim for face_detection module."""

from src.face_detection import (
    best_face,
    crop_face,
    detect_and_encode,
    scan_face,
    capture_from_camera,
    score_face,
    MIN_BLUR,
    MAX_ROLL_DEG,
    MAX_YAW_PROXY,
)

__all__ = [
    "best_face",
    "crop_face",
    "detect_and_encode",
    "scan_face",
    "capture_from_camera",
    "score_face",
    "MIN_BLUR",
    "MAX_ROLL_DEG",
    "MAX_YAW_PROXY",
]
