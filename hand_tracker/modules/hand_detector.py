# ─────────────────────────────────────────────
#  modules/hand_detector.py
#  Compatible mediapipe >= 0.10.30 (Tasks API)
# ─────────────────────────────────────────────

import cv2
import numpy as np
import mediapipe as mp
import urllib.request
import os
import time
from config import (
    MAX_HANDS, DETECTION_CONF, TRACKING_CONF,
    DIST_COEFF, DIST_PROCHE, DIST_LOIN,
    FINGER_TIP_IDS, FINGER_PIP_IDS,
)

MODEL_PATH = "hand_landmarker.task"
MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)

def _ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("[HandDetector] Téléchargement du modèle MediaPipe (~9 Mo)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        print("[HandDetector] Modèle prêt.")


class HandDetector:
    def __init__(self):
        _ensure_model()
        BaseOptions           = mp.tasks.BaseOptions
        HandLandmarker        = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        VisionRunningMode     = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=VisionRunningMode.VIDEO,
            num_hands=MAX_HANDS,
            min_hand_detection_confidence=DETECTION_CONF,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=TRACKING_CONF,
        )
        self._landmarker = HandLandmarker.create_from_options(options)

    def find_hands(self, frame: np.ndarray) -> list:
        rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms    = int(time.time() * 1000)
        result   = self._landmarker.detect_for_video(mp_image, ts_ms)

        hands = []
        if not result.hand_landmarks:
            return hands

        h, w = frame.shape[:2]

        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            raw_side = handedness[0].category_name
            side     = "Right" if raw_side == "Left" else "Left"
            points   = [(int(lm.x * w), int(lm.y * h), lm.z) for lm in landmarks]

            hands.append({
                "raw_landmarks": landmarks,
                "points":   points,
                "fingers":  self._finger_states(points, side),
                "distance": self._estimate_distance(points),
                "side":     side,
                "score":    handedness[0].score,
                "bbox":     self._bounding_box(points),
                "wrist":    points[0],
                "speed":    0.0,
            })
        return hands

    def _finger_states(self, pts, side):
        fingers = {}
        tip, ip = pts[FINGER_TIP_IDS["thumb"]], pts[FINGER_PIP_IDS["thumb"]]
        fingers["thumb"] = tip[0] > ip[0] if side == "Right" else tip[0] < ip[0]
        for name in ["index", "middle", "ring", "pinky"]:
            fingers[name] = pts[FINGER_TIP_IDS[name]][1] < pts[FINGER_PIP_IDS[name]][1]
        return fingers

    def _estimate_distance(self, pts):
        d = float(np.linalg.norm(np.array(pts[0][:2]) - np.array(pts[9][:2])))
        cm = max(5, min(200, int(DIST_COEFF / d) if d > 1 else 999))
        label = "PROCHE" if cm < DIST_PROCHE else "LOIN" if cm > DIST_LOIN else "MOYENNE"
        return {"cm": cm, "label": label, "px": d}

    @staticmethod
    def _bounding_box(pts):
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        return (min(xs), min(ys), max(xs), max(ys))

    @staticmethod
    def hand_angle(hand_data):
        w = np.array(hand_data["points"][0][:2])
        m = np.array(hand_data["points"][9][:2])
        d = m - w
        return float(np.degrees(np.arctan2(-d[1], d[0])))

    @staticmethod
    def pinch_distance(hand_data):
        t = np.array(hand_data["points"][FINGER_TIP_IDS["thumb"]][:2])
        i = np.array(hand_data["points"][FINGER_TIP_IDS["index"]][:2])
        return float(np.linalg.norm(t - i))
