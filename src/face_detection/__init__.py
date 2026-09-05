"""Segment 1: Face Detection, Quality Scoring, and Encoding."""

from .detector import detect_and_encode, crop_face, best_face
from .camera import scan_face
from .quality import (
    score_face,
    MIN_BLUR,
    MAX_ROLL_DEG,
    MAX_YAW_PROXY,
    _laplacian_blur,
    _roll_degrees,
    _yaw_proxy,
)

# Alias for backwards compatibility
capture_from_camera = scan_face

__all__ = [
    "detect_and_encode",
    "crop_face",
    "best_face",
    "scan_face",
    "capture_from_camera",
    "score_face",
    "MIN_BLUR",
    "MAX_ROLL_DEG",
    "MAX_YAW_PROXY",
    "_laplacian_blur",
    "_roll_degrees",
    "_yaw_proxy",
]
