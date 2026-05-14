
import time
import numpy as np
from config import SWIPE_WINDOW, SWIPE_THRESHOLD_PX, FINGER_TIP_IDS


_GESTURE_TABLE: dict[tuple, str] = {
    (True,  True,  True,  True,  True ): "MAIN OUVERTE",
    (False, False, False, False, False): "POING",
    (True,  False, False, False, False): "POUCE LEVE",
    (False, True,  True,  False, False): "PEACE",
    (False, True,  False, False, False): "POINTAGE",
    (False, False, True,  False, False): "DOIGT D HONNEUR",
    (False, True,  True,  True,  True ): "QUATRE DOIGTS",
    (False, False, False, False, True ): "PINKY UP",
    (True,  True,  False, False, True ): "ROCK",
    (True,  True,  True,  True,  False): "QUATRE DOIGTS",
}

_OK_THRESHOLD = 42     
_ORDER = ("thumb", "index", "middle", "ring", "pinky")


class GestureRecognizer:
    def __init__(self):
       
        self._swipe_buf: list[tuple[float, float]] = []  
        
        self._last_swipe_time = 0.0

    def recognize(self, hand_data: dict) -> tuple[str, str | None]:
        """
        Retourne (nom_geste, direction_swipe | None).
        direction_swipe = "GAUCHE" | "DROITE" | None
        """
        fingers = hand_data["fingers"]
        points  = hand_data["points"]
        state   = tuple(fingers[k] for k in _ORDER)

      
        thumb_tip = np.array(points[FINGER_TIP_IDS["thumb"]][:2])
        index_tip = np.array(points[FINGER_TIP_IDS["index"]][:2])
        if float(np.linalg.norm(thumb_tip - index_tip)) < _OK_THRESHOLD:
            gesture = "OK"
        else:
            gesture = _GESTURE_TABLE.get(state, "CUSTOM")

       
        swipe = self._detect_swipe(points[0][0])

        return gesture, swipe

 

    def _detect_swipe(self, wrist_x: float) -> str | None:
        now = time.time()
        self._swipe_buf.append((wrist_x, now))

       
        self._swipe_buf = [
            (x, t) for x, t in self._swipe_buf
            if now - t < SWIPE_WINDOW
        ]

        if len(self._swipe_buf) < 6:
            return None

      
        if now - self._last_swipe_time < 0.6:
            return None

        dx = self._swipe_buf[-1][0] - self._swipe_buf[0][0]
        if abs(dx) >= SWIPE_THRESHOLD_PX:
            self._swipe_buf.clear()
            self._last_swipe_time = now
            return "DROITE" if dx > 0 else "GAUCHE"

        return None
