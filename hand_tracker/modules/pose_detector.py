# modules/pose_detector.py  –  Corps complet multi-personnes v2

import cv2, numpy as np, mediapipe as mp, urllib.request, os, time

POSE_MODEL_PATH = "pose_landmarker.task"
POSE_MODEL_URL  = (
    "https://storage.googleapis.com/mediapipe-models/"
    "pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
)

MAX_PERSONNES = 4

# Connexions squelette complet
CONNEXIONS = [
    # Visage
    (0,1),(1,2),(2,3),(3,7),(0,4),(4,5),(5,6),(6,8),(9,10),
    # Épaules / bras
    (11,12),(11,13),(13,15),(12,14),(14,16),
    # Mains
    (15,17),(15,19),(15,21),(17,19),(16,18),(16,20),(16,22),(18,20),
    # Torse
    (11,23),(12,24),(23,24),
    # Jambes
    (23,25),(25,27),(24,26),(26,28),
    # Pieds
    (27,29),(27,31),(29,31),(28,30),(28,32),(30,32),
]

# Labels membres à afficher
MEMBRES_LABELS = {
    13: "BRAS G",  14: "BRAS D",
    25: "JAMBE G", 26: "JAMBE D",
    15: "POIGNET G", 16: "POIGNET D",
}

# Points de la tête
POINTS_TETE = [0,1,2,3,4,5,6,7,8,9,10]

# Couleur par entité
ENTITE_COULEURS = [
    (0, 210, 140),    # vert   → entité 1
    (0, 140, 255),    # bleu   → entité 2
    (200, 80, 255),   # violet → entité 3
    (0, 220, 255),    # cyan   → entité 4
]


def _ensure_model():
    if not os.path.exists(POSE_MODEL_PATH):
        print("[PoseDetector] Téléchargement du modèle (~5 Mo)...")
        urllib.request.urlretrieve(POSE_MODEL_URL, POSE_MODEL_PATH)
        print("[PoseDetector] Modèle prêt.")


class PoseDetector:
    def __init__(self):
        _ensure_model()
        opts = mp.tasks.vision.PoseLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=POSE_MODEL_PATH),
            running_mode=mp.tasks.vision.RunningMode.VIDEO,
            num_poses=MAX_PERSONNES,
            min_pose_detection_confidence=0.45,
            min_pose_presence_confidence=0.45,
            min_tracking_confidence=0.45,
        )
        self._lm = mp.tasks.vision.PoseLandmarker.create_from_options(opts)
        # Lissage par entité : {idx: [pts_lissés]}
        self._smooth: dict[int, list] = {}
        self._alpha = 0.30

    def detect(self, frame: np.ndarray) -> list[dict]:
        """Retourne une liste de dicts, un par personne détectée."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        res = self._lm.detect_for_video(img, int(time.time() * 1000))

        poses = []
        if not res.pose_landmarks:
            self._smooth.clear()
            return poses

        h, w = frame.shape[:2]

        for idx, lms in enumerate(res.pose_landmarks):
            raw = [(lm.x * w, lm.y * h, lm.z, lm.visibility) for lm in lms]

            # Lissage exponentiel
            if idx not in self._smooth:
                self._smooth[idx] = raw
            else:
                a = self._alpha
                self._smooth[idx] = [
                    (a*r[0]+(1-a)*s[0], a*r[1]+(1-a)*s[1],
                     a*r[2]+(1-a)*s[2], r[3])
                    for r, s in zip(raw, self._smooth[idx])
                ]

            pts = [(int(p[0]), int(p[1]), p[2]) for p in self._smooth[idx]]
            vis = [p[3] for p in self._smooth[idx]]

            tete_box = self._boite_tete(pts, w, h)

            poses.append({
                "idx":       idx,
                "points":    pts,
                "visibility": vis,
                "tete":      pts[0],
                "tete_box":  tete_box,
                "poignet_g": pts[15] if len(pts)>15 else None,
                "poignet_d": pts[16] if len(pts)>16 else None,
                "couleur":   ENTITE_COULEURS[idx % len(ENTITE_COULEURS)],
            })

        # Purge des entités disparues
        actifs = {p["idx"] for p in poses}
        for k in list(self._smooth.keys()):
            if k not in actifs:
                del self._smooth[k]

        return poses

    def _boite_tete(self, pts, w, h) -> tuple | None:
        xs = [pts[i][0] for i in POINTS_TETE if i < len(pts)]
        ys = [pts[i][1] for i in POINTS_TETE if i < len(pts)]
        if not xs:
            return None
        pad = 32
        return (max(0,min(xs)-pad), max(0,min(ys)-pad),
                min(w,max(xs)+pad), min(h,max(ys)+pad))

    # ── Dessin ────────────────────────────────

    @staticmethod
    def draw(frame: np.ndarray, pose: dict, flou_tete: bool = False) -> None:
        pts     = pose["points"]
        vis     = pose["visibility"]
        couleur = pose["couleur"]
        idx     = pose["idx"]

        # ── Squelette ─────────────────────────
        for a, b in CONNEXIONS:
            if a >= len(pts) or b >= len(pts):
                continue
            if vis[a] < 0.35 or vis[b] < 0.35:
                continue
            cv2.line(frame, pts[a][:2], pts[b][:2],
                     couleur, 2, cv2.LINE_AA)

        # ── Points articulaires ───────────────
        for i, pt in enumerate(pts):
            if i >= len(vis) or vis[i] < 0.35:
                continue
            r = 4 if i in MEMBRES_LABELS else 3
            cv2.circle(frame, pt[:2], r, couleur, -1, cv2.LINE_AA)

        # ── Labels membres ────────────────────
        for mid, label in MEMBRES_LABELS.items():
            if mid >= len(pts) or vis[mid] < 0.45:
                continue
            px, py = pts[mid][:2]
            offset_x = -80 if "G" in label else 12
            _lbl(frame, label, (px + offset_x, py), couleur, 0.36)

        # ── Tête ──────────────────────────────
        PoseDetector._draw_tete(frame, pose, couleur, flou_tete)

    @staticmethod
    def _draw_tete(frame, pose, couleur, flou_tete):
        box = pose.get("tete_box")
        if not box:
            return
        x1, y1, x2, y2 = box
        h, w = frame.shape[:2]

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        # Ellipse bien proportionnée autour de la tête
        # Ratio largeur/hauteur naturel ~0.75
        rx = max(12, (x2 - x1) // 2)
        ry = max(16, int(rx * 1.30))

        # Ellipse principale
        cv2.ellipse(frame, (cx, cy), (rx, ry),
                    0, 0, 360, couleur, 2, cv2.LINE_AA)

        # Ellipse intérieure (halo léger)
        alpha_halo = np.zeros_like(frame)
        cv2.ellipse(alpha_halo, (cx, cy), (rx-3, ry-3),
                    0, 0, 360, couleur, 1, cv2.LINE_AA)
        cv2.addWeighted(frame, 1.0, alpha_halo, 0.3, 0, frame)

        # Label ENTITE au-dessus
        idx    = pose["idx"]
        label  = f"ENTITE {idx + 1}"
        lx     = cx - len(label) * 7
        ly     = cy - ry - 18

        # Ligne verticale pointillée tête → label
        for yy in range(cy - ry - 14, cy - ry):
            if yy % 3 == 0:
                cv2.circle(frame, (cx, yy), 1, couleur, -1)

        cv2.putText(frame, label, (lx, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    (0,0,0), 4, cv2.LINE_AA)
        cv2.putText(frame, label, (lx, ly),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62,
                    couleur, 2, cv2.LINE_AA)

        # Flou visage
        if flou_tete:
            PoseDetector._appliquer_flou(frame, (cx-rx, cy-ry, cx+rx, cy+ry), w, h)

    @staticmethod
    def _appliquer_flou(frame, box, w, h):
        x1, y1, x2, y2 = [max(0,v) for v in box]
        x2, y2 = min(w, x2), min(h, y2)
        if x2 <= x1 or y2 <= y1:
            return
        roi     = frame[y1:y2, x1:x2]
        petit   = cv2.resize(roi, (max(1,(x2-x1)//8), max(1,(y2-y1)//8)))
        pixel   = cv2.resize(petit, (x2-x1, y2-y1), interpolation=cv2.INTER_NEAREST)
        flou    = cv2.GaussianBlur(pixel, (25,25), 0)
        masque  = np.zeros((y2-y1, x2-x1), dtype=np.float32)
        cv2.ellipse(masque, ((x2-x1)//2,(y2-y1)//2),
                    ((x2-x1)//2,(y2-y1)//2), 0, 0, 360, 1.0, -1)
        for c in range(3):
            roi[:,:,c] = (roi[:,:,c]*(1-masque)+flou[:,:,c]*masque).astype(np.uint8)
        frame[y1:y2, x1:x2] = roi


def _lbl(frame, texte, pos, couleur, taille=0.38):
    cv2.putText(frame, texte, pos, cv2.FONT_HERSHEY_SIMPLEX,
                taille, (0,0,0), 3, cv2.LINE_AA)
    cv2.putText(frame, texte, pos, cv2.FONT_HERSHEY_SIMPLEX,
                taille, couleur, 1, cv2.LINE_AA)
