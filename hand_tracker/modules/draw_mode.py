

import cv2
import numpy as np
from config import FINGER_TIP_IDS


class DrawMode:
    """
    Canvas de dessin persistant.
    - Index seul levé  → dessine
    - Pause [P]        → arrête le dessin sans effacer
    - Reprise [P]      → continue sur le même dessin
    - Poing fermé      → efface tout
    - Sauvegarde [S]   → exporte en PNG
    """

    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self._canvas    = np.zeros((height, width, 3), dtype=np.uint8)
        self._last_pt:  dict[str, tuple | None] = {}
        self._brush     = 5
        self._paused    = False   
        self._actif     = False   

   

    @property
    def paused(self) -> bool:
        return self._paused

    @property
    def actif(self) -> bool:
        return self._actif

    def toggle_actif(self) -> bool:
        """Active ou désactive le mode dessin. Retourne le nouvel état."""
        self._actif  = not self._actif
        self._paused = False
        if not self._actif:
            self._last_pt.clear()
        return self._actif

    def toggle_pause(self) -> bool:
        """Met en pause ou reprend le dessin. Retourne l'état de pause."""
        if not self._actif:
            return False
        self._paused = not self._paused
        if self._paused:
            self._last_pt.clear()
        return self._paused



    def update(self, hand_data: dict, color: tuple,
               hand_id: str, gesture: str) -> None:
        if not self._actif or self._paused:
            self._last_pt[hand_id] = None
            return

        fingers = hand_data["fingers"]
        points  = hand_data["points"]

        if gesture == "POING":
            self.clear()
            self._last_pt[hand_id] = None
            return

        is_drawing = fingers["index"] and not fingers["middle"]
        tip = points[FINGER_TIP_IDS["index"]][:2]

        if is_drawing:
            prev = self._last_pt.get(hand_id)
            if prev is not None:
                cv2.line(self._canvas, prev, tip,
                         color, self._brush, cv2.LINE_AA)
            else:
                cv2.circle(self._canvas, tip, self._brush // 2, color, -1)
            self._last_pt[hand_id] = tip
        else:
            self._last_pt[hand_id] = None

    def overlay(self, frame: np.ndarray, alpha: float = 0.80) -> None:
        mask = cv2.cvtColor(self._canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(mask, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        bg  = cv2.bitwise_and(frame, frame, mask=mask_inv)
        fg  = cv2.bitwise_and(self._canvas, self._canvas, mask=mask)
        blended = cv2.addWeighted(fg, alpha, np.zeros_like(fg), 0, 0)
        np.copyto(frame, cv2.add(bg, blended))

    def draw_status(self, frame: np.ndarray) -> None:
        """Affiche l'état du dessin dans le coin bas droite."""
        if not self._actif:
            return
        h, w = frame.shape[:2]
        if self._paused:
            txt = "DESSIN : EN PAUSE  [P] reprendre"
            col = (0, 160, 255)
        else:
            txt = "DESSIN : ACTIF  [P] pause  poing = effacer"
            col = (0, 230, 130)
        cv2.putText(frame, txt, (w - 460, h - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44,
                    (0,0,0), 3, cv2.LINE_AA)
        cv2.putText(frame, txt, (w - 460, h - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44,
                    col, 1, cv2.LINE_AA)

    def clear(self) -> None:
        self._canvas[:] = 0

    def save(self, path: str = "dessin.png") -> None:
        cv2.imwrite(path, self._canvas)
        print(f"[DrawMode] Dessin sauvegardé → {path}")
