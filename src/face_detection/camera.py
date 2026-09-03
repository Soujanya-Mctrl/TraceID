"""
Live face scan via webcam.

Two-tier design:
  - Fast Haar cascade drives the LIVE preview loop (cheap, real-time).
  - Once the face is stably detected for STABLE_FRAMES_REQUIRED frames,
    we capture that frame and hand it to the real pipeline
    (face_detection.best_face -> DeepFace/MTCNN) for the actual
    detection + 512-D encoding used downstream.

This avoids running DeepFace on every webcam frame, which would be
too slow for a live preview.
"""

import cv2
import time
import os
import sys

from .detector import best_face, crop_face

STABLE_FRAMES_REQUIRED = 20   # ~1-1.5s at 15-20fps
MOVEMENT_TOLERANCE_PX = 25    # how much the face box can drift and still count as "stable"
DEFAULT_CAPTURE_PATH = os.path.join("output", "live_capture.jpg")
DEFAULT_CROP_PATH = os.path.join("output", "live_face_crop.jpg")


def _face_center(box):
    x, y, w, h = box
    return (x + w // 2, y + h // 2)


def get_haar_cascade():
    """Locates and loads the Haar frontalface cascade classifier."""
    cascade_paths = [
        os.path.join(os.path.dirname(__file__), "data", "haarcascade_frontalface_default.xml"),
        getattr(cv2, "data", None) and os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"),
        "haarcascade_frontalface_default.xml",
    ]

    for p in cascade_paths:
        if p and os.path.exists(p):
            try:
                cascade = cv2.CascadeClassifier(p)
                if not cascade.empty():
                    return cascade
            except Exception:
                pass

    try:
        # Fallback to default cv2.data
        return cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    except Exception:
        return None


def scan_face(
    camera_index: int = 0,
    capture_path: str = DEFAULT_CAPTURE_PATH,
    crop_path: str = DEFAULT_CROP_PATH,
    show_window: bool = True,
):
    """
    Executes live webcam face scanning with real-time Haar overlay and stability check,
    then executes DeepFace/MTCNN detection and 512-D encoding on the final captured frame.
    """
    os.makedirs(os.path.dirname(capture_path) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(crop_path) or ".", exist_ok=True)

    face_cascade = get_haar_cascade()

    backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY
    cap = cv2.VideoCapture(camera_index, backend)
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(f"Could not open webcam on device #{camera_index}.")

    stable_count = 0
    last_center = None
    captured_frame = None

    print("\n[Live Camera Scan] Scanning... Look at the camera and hold still.")
    print("  * Fast Haar cascade tracking active (30+ FPS).")
    print("  * Hold face steady inside box for 1-1.5s, or press [SPACE] to capture immediately.")
    print("  * Press [Q] or [ESC] to cancel.\n")

    try:
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                time.sleep(0.05)
                continue

            display = frame.copy()
            h_f, w_f = frame.shape[:2]

            # Fast Haar cascade detection if available
            faces = []
            if face_cascade is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
                )

            if len(faces) == 1:
                box = faces[0]
                center = _face_center(box)
                x, y, w, h = box
                cv2.rectangle(display, (x, y), (x + w, y + h), (0, 255, 0), 2)

                if last_center is not None:
                    dist = ((center[0] - last_center[0]) ** 2 + (center[1] - last_center[1]) ** 2) ** 0.5
                    if dist <= MOVEMENT_TOLERANCE_PX:
                        stable_count += 1
                    else:
                        stable_count = 0
                last_center = center

                cv2.putText(
                    display, f"Hold still: {stable_count}/{STABLE_FRAMES_REQUIRED}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                )

                if stable_count >= STABLE_FRAMES_REQUIRED:
                    print(f"[Live Camera Scan] Face stabilized ({STABLE_FRAMES_REQUIRED} frames). Snapping frame!")
                    captured_frame = frame.copy()
                    break
            elif len(faces) > 1:
                stable_count = 0
                last_center = None
                for (x, y, w, h) in faces:
                    cv2.rectangle(display, (x, y), (x + w, y + h), (0, 165, 255), 2)
                cv2.putText(display, "Multiple faces - only one person please", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                # No Haar face detected or cascade not available; display alignment guide
                stable_count = 0
                last_center = None
                cx, cy = w_f // 2, h_f // 2
                cv2.ellipse(display, (cx, cy), (int(w_f * 0.22), int(h_f * 0.35)), 0, 0, 360, (0, 200, 255), 1)
                cv2.putText(display, "Position face in view (Press SPACE to capture)", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 200, 255), 2)

            if show_window:
                cv2.imshow("Face Scan - Press SPACE to capture, Q to cancel", display)
                key = cv2.waitKey(1) & 0xFF
                if key == 32:  # SPACE key manual snap
                    print("[Live Camera Scan] Manual capture triggered via SPACE key.")
                    captured_frame = frame.copy()
                    break
                elif key in (ord("q"), ord("Q"), 27):
                    raise RuntimeError("Scan cancelled by user.")
            else:
                # Headless auto-snap after 10 frames
                time.sleep(0.05)
                stable_count += 1
                if stable_count >= 10:
                    captured_frame = frame.copy()
                    break

    finally:
        cap.release()
        if show_window:
            try:
                cv2.destroyAllWindows()
            except Exception:
                pass

    if captured_frame is None:
        raise RuntimeError("Scan did not complete.")

    cv2.imwrite(capture_path, captured_frame)
    print(f"[Live Camera Scan] Saved captured frame to: {capture_path}")

    # Now run the REAL detection/encoding pass (DeepFace/MTCNN) on the
    # captured frame, instead of trusting the cheap Haar cascade.
    print("[Live Camera Scan] Running DeepFace (MTCNN + Facenet512) on captured frame...")
    try:
        face = best_face(capture_path)
    except Exception as e:
        if os.path.exists(capture_path):
            os.remove(capture_path)
        raise RuntimeError(
            f"Captured frame failed real detection ({e}). Try scanning again with better lighting."
        )

    crop_face(capture_path, face["facial_area"], crop_path, padding=0.3)
    print(f"[Live Camera Scan] DeepFace Confirmed: Confidence {face['confidence']} | Crop saved to: {crop_path}")

    return {
        "image_path": capture_path,
        "face_crop_path": crop_path,
        "face_embedding": face["embedding"].tolist(),
        "face_confidence": face["confidence"],
    }


if __name__ == "__main__":
    result = scan_face()
    print(f"\n[Result] Captured Image: {result['image_path']}")
    print(f"[Result] 30% Padded Crop: {result['face_crop_path']}")
    print(f"[Result] DeepFace Confidence: {result['face_confidence']}")
    print(f"[Result] Embedding Length: {len(result['face_embedding'])}")
