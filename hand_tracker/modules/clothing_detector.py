

import cv2
import numpy as np
import time


class ClothingDetector:
    """
    Analyse les régions du corps définies par les landmarks Pose
    pour détecter les accessoires / vêtements portés.
    Met à jour toutes les N frames pour ne pas charger le CPU.
    """

    UPDATE_EVERY = 12   

    def __init__(self):
        self._frame_count = 0
       
        self._cache: dict[int, dict] = {}
        
        self._eye_cascade = None
        try:
            import cv2
            self._eye_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_eye_tree_eyeglasses.xml"
            )
        except Exception:
            pass

    def update(self, frame: np.ndarray, poses: list) -> list[dict]:
        """
        Retourne une liste de dicts d'attributs pour chaque pose.
        dict keys : lunettes, casquette, haut, bas, couleur_haut, couleur_bas
        """
        self._frame_count += 1
        if self._frame_count % self.UPDATE_EVERY != 0:
            return [self._cache.get(i, self._vide()) for i in range(len(poses))]

        resultats = []
        for i, pose in enumerate(poses):
            attrs = self._analyser(frame, pose)
            self._cache[i] = attrs
            resultats.append(attrs)
        return resultats



    def _analyser(self, frame: np.ndarray, pose: dict) -> dict:
        h, w = frame.shape[:2]
        pts  = pose["points"]

        attrs = self._vide()

     
        attrs["casquette"] = self._detecter_casquette(frame, pose, w, h)

     
        attrs["lunettes"] = self._detecter_lunettes(frame, pose, w, h)

    
        haut = self._analyser_haut(frame, pts, w, h)
        attrs["haut"]          = haut["type"]
        attrs["couleur_haut"]  = haut["couleur"]

   
        bas = self._analyser_bas(frame, pts, w, h)
        attrs["bas"]           = bas["type"]
        attrs["couleur_bas"]   = bas["couleur"]

        return attrs

  

    def _detecter_casquette(self, frame, pose, w, h) -> bool:
        """
        Si la zone au-dessus de la tête est significativement plus sombre
        ou plus uniforme que le visage, probablement une casquette.
        """
        box = pose.get("tete_box")
        if not box:
            return False
        x1, y1, x2, y2 = box
        head_h = y2 - y1

     
        zone_y1 = max(0, y1 - int(head_h * 0.5))
        zone_y2 = max(0, y1 + int(head_h * 0.1))
        zone_x1 = max(0, x1 + (x2-x1)//4)
        zone_x2 = min(w, x2 - (x2-x1)//4)

        if zone_y2 <= zone_y1 or zone_x2 <= zone_x1:
            return False

        region = frame[zone_y1:zone_y2, zone_x1:zone_x2]
        if region.size == 0:
            return False

       
        fy1, fy2 = max(0,y1), min(h, y1 + head_h//2)
        fx1, fx2 = max(0,x1), min(w, x2)
        face_region = frame[fy1:fy2, fx1:fx2]
        if face_region.size == 0:
            return False

        cap_dark   = float(np.mean(region))
        face_light = float(np.mean(face_region))


        cap_std = float(np.std(region))
        return (face_light - cap_dark > 35) and (cap_std < 55)

  

    def _detecter_lunettes(self, frame, pose, w, h) -> bool:
        box = pose.get("tete_box")
        if not box:
            return False
        x1, y1, x2, y2 = box
        head_h = y2 - y1


        ey1 = max(0, y1 + int(head_h * 0.25))
        ey2 = max(0, y1 + int(head_h * 0.55))
        ex1 = max(0, x1)
        ex2 = min(w, x2)

        if ey2 <= ey1 or ex2 <= ex1:
            return False

        region = frame[ey1:ey2, ex1:ex2]
        if region.size == 0:
            return False

  
        if self._eye_cascade is not None:
            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            eyes = self._eye_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(10, 10)
            )
            if len(eyes) >= 2:
                return True

 
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        h_lines  = float(np.sum(np.abs(sobel_x) > 80))
        total    = float(region.shape[0] * region.shape[1])
        return (h_lines / max(1, total)) > 0.06



    def _analyser_haut(self, frame, pts, w, h) -> dict:
    
        idxs = [11, 12, 23, 24]  
        coords = [pts[i] for i in idxs if i < len(pts)]
        if len(coords) < 3:
            return {"type": "?", "couleur": "?"}

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        x1, x2 = max(0, min(xs)), min(w, max(xs))
        y1, y2 = max(0, min(ys)), min(h, max(ys))

        if x2 <= x1 or y2 <= y1:
            return {"type": "t-shirt", "couleur": "?"}

        region = frame[y1:y2, x1:x2]
        if region.size == 0:
            return {"type": "t-shirt", "couleur": "?"}

        couleur = self._nom_couleur(region)

     
        hauteur_px = y2 - y1
        type_haut  = "t-shirt" if hauteur_px < (h * 0.35) else "veste"

        return {"type": type_haut, "couleur": couleur}

    

    def _analyser_bas(self, frame, pts, w, h) -> dict:
        idxs = [23, 24, 25, 26]
        coords = [pts[i] for i in idxs if i < len(pts)]
        if len(coords) < 2:
            return {"type": "?", "couleur": "?"}

        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        x1, x2 = max(0, min(xs)), min(w, max(xs))
        y1, y2 = max(0, min(ys)), min(h, max(ys))

        if x2 <= x1 or y2 <= y1:
            return {"type": "pantalon", "couleur": "?"}

        region = frame[y1:y2, x1:x2]
        if region.size == 0:
            return {"type": "pantalon", "couleur": "?"}

        couleur = self._nom_couleur(region)

     
        hauteur_px = y2 - y1
        type_bas   = "short" if hauteur_px < (h * 0.15) else "pantalon"

        return {"type": type_bas, "couleur": couleur}

  

    @staticmethod
    def _nom_couleur(region: np.ndarray) -> str:
        """Retourne le nom approximatif de la couleur dominante."""
        avg = region.mean(axis=(0, 1))  # B, G, R
        b, g, r = float(avg[0]), float(avg[1]), float(avg[2])

        lum = (r + g + b) / 3
        sat = max(r, g, b) - min(r, g, b)

        if lum < 45:
            return "noir"
        if lum > 200 and sat < 35:
            return "blanc"
        if sat < 35:
            return "gris"
        if r > g and r > b:
            return "rouge" if r > 140 else "bordeaux"
        if g > r and g > b:
            return "vert"
        if b > r and b > g:
            return "bleu"
        if r > 160 and g > 120 and b < 80:
            return "orange"
        if r > 150 and g > 150 and b < 80:
            return "jaune"
        if r > 130 and b > 130 and g < 100:
            return "violet"
        return "mixte"

    @staticmethod
    def _vide() -> dict:
        return {
            "lunettes":     False,
            "casquette":    False,
            "haut":         "?",
            "couleur_haut": "?",
            "bas":          "?",
            "couleur_bas":  "?",
        }
