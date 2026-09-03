"""Segment 1: Face Detection and Encoding."""

from .detector import detect_and_encode, crop_face, best_face
from .camera import scan_face

# Alias for backwards compatibility
capture_from_camera = scan_face

__all__ = ["detect_and_encode", "crop_face", "best_face", "scan_face", "capture_from_camera"]
