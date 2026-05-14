import cv2
import numpy as np
import os
import time

CHEMIN_DEFAUT = "photo.png"   
FONDU_DUREE   = 0.4          


class ImageOverlay:
    def __init__(self, chemin: str = CHEMIN_DEFAUT):
        self._chemin = chemin
        self._img    = self._charger(chemin)
        self._alpha  = 0.0          # 0 = invisible, 1 = plein
        self._actif  = False        # True = doit être visible
        self._t_last = time.time()

 

    def activer(self):
        self._actif = True

    def desactiver(self):
        self._actif = False

    def dessiner(self, frame: np.ndarray) -> None:
        """Applique l'image sur le frame avec fondu."""
        now = time.time()
        dt  = now - self._t_last
        self._t_last = now

        # Mise à jour de l'alpha (fondu entrée/sortie)
        vitesse = dt / max(FONDU_DUREE, 0.01)
        if self._actif:
            self._alpha = min(1.0, self._alpha + vitesse)
        else:
            self._alpha = max(0.0, self._alpha - vitesse)

        if self._alpha <= 0.01:
            return

        if self._img is None:
            self._dessiner_placeholder(frame)
            return

        self._appliquer_image(frame)

    def recharger(self, chemin: str) -> None:
        """Charge une nouvelle image."""
        self._chemin = chemin
        self._img    = self._charger(chemin)


    def _charger(self, chemin: str):
        if not os.path.exists(chemin):
            print(f"[ImageOverlay] Fichier introuvable : {chemin}")
            print("[ImageOverlay] Place ton image dans le dossier hand_tracker/ avec le nom 'photo.png'")
            return None
        img = cv2.imread(chemin, cv2.IMREAD_UNCHANGED)
        if img is None:
            print(f"[ImageOverlay] Impossible de lire : {chemin}")
        return img

    def _appliquer_image(self, frame: np.ndarray) -> None:
        fh, fw = frame.shape[:2]

        # Redimensionne l'image pour tenir dans 40% du frame, centré en haut
        max_w = int(fw * 0.40)
        max_h = int(fh * 0.40)
        img_r = self._redim(self._img, max_w, max_h)

        ih, iw = img_r.shape[:2]
        x = (fw - iw) // 2
        y = 20

        if x < 0 or y < 0 or x + iw > fw or y + ih > fh:
            return

        roi    = frame[y:y+ih, x:x+iw]

   
        if img_r.shape[2] == 4:
            alpha_masque = (img_r[:,:,3] / 255.0) * self._alpha
            img_rgb      = img_r[:,:,:3]
        else:
            alpha_masque = np.full((ih, iw), self._alpha)
            img_rgb      = img_r

        for c in range(3):
            roi[:,:,c] = (roi[:,:,c] * (1 - alpha_masque)
                          + img_rgb[:,:,c] * alpha_masque).astype(np.uint8)
        frame[y:y+ih, x:x+iw] = roi

       
        ep = max(0, int(2 * self._alpha))
        if ep > 0:
            cv2.rectangle(frame, (x-ep, y-ep), (x+iw+ep, y+ih+ep),
                          (255, 255, 255), ep, cv2.LINE_AA)

    def _dessiner_placeholder(self, frame: np.ndarray) -> None:
        """Si aucune image chargée, affiche un message."""
        fh, fw = frame.shape[:2]
        msg  = "photo.png introuvable"
        cx   = fw // 2 - len(msg) * 6
        cy   = 60
        a    = self._alpha
        col  = tuple(int(c * a) for c in (0, 220, 255))
        cv2.putText(frame, msg, (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,0,0), 4, cv2.LINE_AA)
        cv2.putText(frame, msg, (cx, cy),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, col,   2, cv2.LINE_AA)

    @staticmethod
    def _redim(img, max_w, max_h):
        ih, iw = img.shape[:2]
        scale  = min(max_w / iw, max_h / ih)
        nw, nh = int(iw * scale), int(ih * scale)
        return cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
