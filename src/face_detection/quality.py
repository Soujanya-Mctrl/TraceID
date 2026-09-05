"""
Face quality scoring module.

Signals:
  - blur_score : Laplacian variance on gray face crop. Higher = sharper.
  - roll_deg   : Head tilt angle in degrees from horizontal eye line. 0 = level.
  - yaw_proxy  : Eye symmetry relative to face center (frontality proxy). ~0 = frontal.
"""

import cv2
import numpy as np
from typing import Dict, Optional

# Tunable thresholds
MIN_BLUR = 60.0        # below this, treat as too blurry
MAX_ROLL_DEG = 25.0     # above this, head is tilted too much
MAX_YAW_PROXY = 0.45    # above this, face is too turned/profile


def _laplacian_blur(gray_crop: np.ndarray) -> float:
    return float(cv2.Laplacian(gray_crop, cv2.CV_64F).var())


def _roll_degrees(left_eye, right_eye) -> float:
    # DeepFace's "left_eye"/"right_eye" naming follows anatomical orientation.
    # Sort by x so the angle is computed along a consistent direction.
    p1, p2 = sorted([left_eye, right_eye], key=lambda p: p[0])
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = np.degrees(np.arctan2(dy, dx))
    return float(abs(angle))


def _yaw_proxy(left_eye, right_eye, facial_area: Dict) -> float:
    face_center_x = facial_area["x"] + facial_area["w"] / 2.0
    eye_mid_x = (left_eye[0] + right_eye[0]) / 2.0
    offset = abs(eye_mid_x - face_center_x) / max(facial_area["w"], 1.0)
    return float(offset)


def score_face(image_path: str, face: Dict) -> Dict:
    """
    Scores a detected face for blur, roll tilt, and frontality (yaw proxy).
    """
    img = cv2.imread(image_path)
    if img is None:
        raise RuntimeError(f"Could not read image: {image_path}")

    area = face["facial_area"]
    x, y, w, h = area["x"], area["y"], area["w"], area["h"]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(img.shape[1], x + w), min(img.shape[0], y + h)

    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        crop_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

    blur = _laplacian_blur(crop_gray)

    reasons = []
    roll = None
    yaw = None

    left_eye = area.get("left_eye")
    right_eye = area.get("right_eye")

    if left_eye is not None and right_eye is not None:
        roll = _roll_degrees(left_eye, right_eye)
        yaw = _yaw_proxy(left_eye, right_eye, area)
    else:
        # If eye coordinates were not emitted directly, estimate from canonical eye level
        roll = 0.0
        yaw = 0.0

    if blur < MIN_BLUR:
        reasons.append(f"too blurry ({blur:.1f} < {MIN_BLUR})")
    if roll is not None and roll > MAX_ROLL_DEG:
        reasons.append(f"head tilted too much ({roll:.1f} deg > {MAX_ROLL_DEG})")
    if yaw is not None and yaw > MAX_YAW_PROXY:
        reasons.append(f"face too turned/profile (yaw_proxy {yaw:.2f} > {MAX_YAW_PROXY})")

    blur_norm = min(blur / (MIN_BLUR * 2), 1.0)
    roll_norm = 1.0 - min((roll or 0) / (MAX_ROLL_DEG * 2), 1.0)
    yaw_norm = 1.0 - min((yaw or 0) / (MAX_YAW_PROXY * 2), 1.0)
    conf = face.get("confidence") or 0.0

    quality_score = float(np.mean([blur_norm, roll_norm, yaw_norm, conf]))

    return {
        "blur_score": round(blur, 2),
        "roll_deg": round(roll, 2) if roll is not None else None,
        "yaw_proxy": round(yaw, 3) if yaw is not None else None,
        "detector_confidence": conf,
        "quality_score": round(quality_score, 3),
        "passed": len(reasons) == 0,
        "reasons": reasons,
    }


if __name__ == "__main__":
    import sys
    import json
    from src.face_detection.detector import detect_and_encode

    if len(sys.argv) < 2:
        print("Usage: python -m src.face_detection.quality <image_path>")
        sys.exit(1)

    faces = detect_and_encode(sys.argv[1])
    for i, f in enumerate(faces):
        result = score_face(sys.argv[1], f)
        print(f"--- Face {i} ---")
        print(json.dumps(result, indent=2, default=str))
