

import cv2, numpy as np, time
from modules.visual_effects import draw_corner_bracket


def _txt(frame, texte, pos, couleur=(220,220,220), taille=0.55, ep=1):
    cv2.putText(frame, texte, pos, cv2.FONT_HERSHEY_SIMPLEX,
                taille, (0,0,0), ep+2, cv2.LINE_AA)
    cv2.putText(frame, texte, pos, cv2.FONT_HERSHEY_SIMPLEX,
                taille, couleur, ep, cv2.LINE_AA)


def _rect_alpha(frame, x1, y1, x2, y2, alpha=0.65, color=(6,6,18)):
    x1,y1,x2,y2 = max(0,x1),max(0,y1),min(frame.shape[1],x2),min(frame.shape[0],y2)
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0: return
    fond = np.full_like(roi, color)
    cv2.addWeighted(fond, alpha, roi, 1-alpha, 0, roi)
    frame[y1:y2, x1:x2] = roi


class HUD:
    def __init__(self, largeur: int, hauteur: int):
        self.w, self.h = largeur, hauteur
        self._fps_buf  = []
        self._last_t   = time.time()
        self._fps      = 0

    def tick_fps(self) -> int:
        now = time.time()
        dt  = now - self._last_t
        self._last_t = now
        if dt > 0:
            self._fps_buf.append(1.0/dt)
            if len(self._fps_buf)>40: self._fps_buf.pop(0)
        self._fps = int(sum(self._fps_buf)/max(1,len(self._fps_buf)))
        return self._fps

    def show_swipe(self, *a): pass   

 

    def draw(self, frame, mains, gestes, modes,
             poses=None, clothing=None, extra=None):
        w, h = self.w, self.h

   
        _rect_alpha(frame, 0, 0,    w, 50)
        _rect_alpha(frame, 0, h-48, w, h)

      
        draw_corner_bracket(frame, 8, 8, w-17, h-17,
                            (0,170,110), size=22, thickness=2)

    
        col = (0,220,80) if self._fps>=25 else (0,180,255) if self._fps>=15 else (0,60,220)
        _txt(frame, f"FPS {self._fps:03d}", (16, 34), col, 0.70, 2)

        
        titre = "SUIVI CORPOREL  + mains"
        _txt(frame, titre, (w//2 - len(titre)*7, 34), (100,200,255), 0.68, 2)

        # Statut tracking
        dot = (0,230,80) if (mains or poses) else (0,60,200)
        cv2.circle(frame, (w-22, 28), 7, dot, -1, cv2.LINE_AA)
        cv2.circle(frame, (w-22, 28), 9, dot,  1, cv2.LINE_AA)

        # Modes 
        self._draw_modes(frame, modes, w)

        # Bas : gestes mains
        for i,(md,geste) in enumerate(zip(mains, gestes)):
            if geste and geste != "CUSTOM":
                gx = w//2 - 100 + i*130
                _txt(frame, geste, (gx, h-14), (0,215,160), 0.62, 2)

        # Bas gauche : nb entités
        nb = len(poses) if poses else 0
        _txt(frame, f"ENTITES : {nb}   MAINS : {len(mains)}",
             (16, h-28), (150,150,200), 0.48)

        _txt(frame, "Q/ECHAP=fermer  D=dessin  P=pause  B=flou",
             (16, h-12), (70,70,70), 0.36)

        # Fiches entités 
        if poses and clothing:
            self._draw_fiches(frame, poses, clothing, h)

  

    def _draw_modes(self, frame, modes, w):
        defs = [
            ("D", "DESSIN",  "draw"),
            ("P", "PAUSE",   "draw_pause"),
            ("B", "FLOU",    "blur"),
            ("C", "EFFACER", None),
        ]
        panel_x = w - 138
        panel_w = 130
        _rect_alpha(frame, panel_x-6, 56, panel_x+panel_w, 56+len(defs)*30+8,
                    0.70, (4,4,16))
        cv2.rectangle(frame, (panel_x-6,56), (panel_x+panel_w, 56+len(defs)*30+8),
                      (0,100,60), 1)

        for i,(key,lab,cle) in enumerate(defs):
            by = 72 + i*30
            actif = modes.get(cle, False) if cle else False

            # Fond case actif
            if actif:
                _rect_alpha(frame, panel_x-4, by-16, panel_x+panel_w-2, by+8,
                            0.80, (0,50,25))
                cv2.rectangle(frame, (panel_x-4,by-16),
                              (panel_x+panel_w-2, by+8), (0,160,80), 1)

            # Touche
            col_key = (180,180,180)
            _txt(frame, f"[{key}]", (panel_x, by), col_key, 0.42)

            # Label
            col_lab = (0,230,130) if actif else (90,90,90)
            _txt(frame, lab, (panel_x+36, by), col_lab, 0.42)

            # Point état
            if cle is not None:
                dot_c = (0,210,90) if actif else (50,50,50)
                cv2.circle(frame, (panel_x+panel_w-8, by-4),
                           5, dot_c, -1, cv2.LINE_AA)


    def _draw_fiches(self, frame, poses, clothing, h):
        FICHE_W = 175
        FICHE_H = 148
        MARGE   = 12
        START_Y = 60

        for idx, (pose, attrs) in enumerate(zip(poses, clothing)):
            x1 = MARGE
            y1 = START_Y + idx * (FICHE_H + 10)
            y2 = y1 + FICHE_H

            if y2 > h - 50:
                break

            couleur = pose["couleur"]

            # Fond fiche
            _rect_alpha(frame, x1, y1, x1+FICHE_W, y2, 0.72, (4,4,20))
            cv2.rectangle(frame, (x1,y1), (x1+FICHE_W,y2), couleur, 1)

            # En-tête fiche
            titre = f"ENTITE {idx+1}"
            cv2.putText(frame, titre, (x1+8, y1+18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (0,0,0), 4, cv2.LINE_AA)
            cv2.putText(frame, titre, (x1+8, y1+18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        couleur, 2, cv2.LINE_AA)

            # Séparateur
            cv2.line(frame, (x1+6, y1+24), (x1+FICHE_W-6, y1+24),
                     couleur, 1)

            # Attributs
            lignes = [
                ("LUNETTES",  "OUI" if attrs["lunettes"]  else "NON",
                 (0,200,120) if attrs["lunettes"]  else (80,80,80)),
                ("CASQUETTE", "OUI" if attrs["casquette"] else "NON",
                 (0,200,120) if attrs["casquette"] else (80,80,80)),
                ("HAUT",      f"{attrs['haut']} {attrs['couleur_haut']}",
                 (180,220,255)),
                ("BAS",       f"{attrs['bas']} {attrs['couleur_bas']}",
                 (180,220,255)),
            ]

            for j,(clé,valeur,col_v) in enumerate(lignes):
                ty = y1 + 40 + j*24
                # Clé en gris
                cv2.putText(frame, clé, (x1+8, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                            (0,0,0), 3, cv2.LINE_AA)
                cv2.putText(frame, clé, (x1+8, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                            (110,110,110), 1, cv2.LINE_AA)
                # Valeur colorée
                cv2.putText(frame, valeur, (x1+80, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                            (0,0,0), 3, cv2.LINE_AA)
                cv2.putText(frame, valeur, (x1+80, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38,
                            col_v, 1, cv2.LINE_AA)

            # Coin fiche
            draw_corner_bracket(frame, x1, y1, FICHE_W, FICHE_H,
                                couleur, size=8, thickness=1)
