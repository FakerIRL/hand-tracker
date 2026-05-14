import time
import numpy as np

FENETRE      = 1.8    
MIN_CYCLES   = 2     
AMPLITUDE_PX = 30     
COOLDOWN     = 0.3   


class WaveDetector:
    def __init__(self):
       
        self._hist: dict[str, list] = {"Left": [], "Right": []}
        self._actif      = False
        self._last_check = 0.0

    def update(self, mains: list, pose_data: dict | None) -> bool:
        """
        Met à jour avec les positions des mains.
        Retourne True si le geste six-seven est en cours.
        """
        now = time.time()

       
        positions = {}
        for md in mains:
            side = md["side"]  
            positions[side] = float(md["wrist"][1])

       
        if pose_data:
            if "Left"  not in positions:
                positions["Left"]  = float(pose_data["poignet_g"][1])
            if "Right" not in positions:
                positions["Right"] = float(pose_data["poignet_d"][1])

       
        for side, y in positions.items():
            self._hist[side].append((y, now))

       
        for side in self._hist:
            self._hist[side] = [
                (y, t) for y, t in self._hist[side]
                if now - t < FENETRE
            ]

       
        if now - self._last_check < 0.1:
            return self._actif
        self._last_check = now

        if len(self._hist["Left"]) < 8 or len(self._hist["Right"]) < 8:
            self._actif = False
            return False

        ok_g = self._compte_oscillations(self._hist["Left"])
        ok_d = self._compte_oscillations(self._hist["Right"])

        self._actif = (ok_g >= MIN_CYCLES and ok_d >= MIN_CYCLES)
        return self._actif

    def _compte_oscillations(self, hist: list) -> int:
        """Compte le nombre de pics (montée + descente) dans l'historique."""
        ys = np.array([h[0] for h in hist])

   
        if len(ys) > 5:
            kernel = np.ones(5) / 5
            ys = np.convolve(ys, kernel, mode="same")

      
        directions = np.sign(np.diff(ys))
        directions = directions[directions != 0

        if len(directions) < 2:
            return 0

        
        changements = np.sum(np.diff(directions) != 0)

       
        amplitude = float(np.max(ys) - np.min(ys))
        if amplitude < AMPLITUDE_PX:
            return 0

        return changements // 2

    def reset(self):
        self._hist  = {"Left": [], "Right": []}
        self._actif = False
