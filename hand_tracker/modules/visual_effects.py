

import cv2
import numpy as np
from config import SKELETON_CHAINS, FINGER_TIP_IDS, GESTURE_COLORS


def get_gesture_color(gesture: str) -> tuple:
    return GESTURE_COLORS.get(gesture, GESTURE_COLORS["default"])


def draw_hand_skeleton(frame: np.ndarray, hand_data: dict, color: tuple) -> None:
    """Dessine les os et articulations de la main (style simple)."""
    pts = hand_data["points"]

   
    for chain in SKELETON_CHAINS:
        for i in range(len(chain) - 1):
            cv2.line(frame, pts[chain[i]][:2], pts[chain[i+1]][:2],
                     color, 2, cv2.LINE_AA)

   
    tips = set(FINGER_TIP_IDS.values())
    for idx, pt in enumerate(pts):
        taille = 7 if idx in tips else 4
        cv2.circle(frame, pt[:2], taille, color, -1, cv2.LINE_AA)


def draw_finger_labels(frame: np.ndarray, hand_data: dict) -> None:
    """Affiche le nom des doigts levés en français."""
    noms = {
        "thumb":  "POUCE",
        "index":  "INDEX",
        "middle": "MAJEUR",
        "ring":   "ANNULAIRE",
        "pinky":  "AURICULAIRE",
    }
    pts     = hand_data["points"]
    fingers = hand_data["fingers"]
    for name, label in noms.items():
        if not fingers.get(name):
            continue
        fid = FINGER_TIP_IDS[name]
        x, y = pts[fid][0] + 12, pts[fid][1] - 5
        cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (0, 0, 0), 3, cv2.LINE_AA)
        cv2.putText(frame, label, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.45, (230, 255, 200), 1, cv2.LINE_AA)


def draw_corner_bracket(frame, x, y, w, h, color, size=20, thickness=2):
    """Coins carrés autour d'une zone."""
    for dx, dy in [(0,0),(w,0),(0,h),(w,h)]:
        sx = -size if dx == w else size
        sy = -size if dy == h else size
        cv2.line(frame, (x+dx, y+dy), (x+dx+sx, y+dy),   color, thickness, cv2.LINE_AA)
        cv2.line(frame, (x+dx, y+dy), (x+dx,    y+dy+sy), color, thickness, cv2.LINE_AA)



class Trail:
    def update(self, *a): pass
    def draw(self, *a):   pass
    def clear(self):      pass

class ParticleSystem:
    def emit(self, *a):            pass
    def update_and_draw(self, *a): pass
    def clear(self):               pass
