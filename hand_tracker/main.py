import sys, cv2, numpy as np, time

from config import CAM_INDEX, CAM_WIDTH, CAM_HEIGHT, CAM_FPS
from modules.hand_detector      import HandDetector
from modules.pose_detector      import PoseDetector
from modules.gesture_recognizer import GestureRecognizer
from modules.clothing_detector  import ClothingDetector
from modules.visual_effects     import get_gesture_color, draw_hand_skeleton, draw_finger_labels
from modules.hud                import HUD
from modules.draw_mode          import DrawMode

MODES = {
    "draw":       False,
    "draw_pause": False,
    "blur":       False,
}

AIDE = """
- Raccourcis
  [D]  Activer / désactiver le dessin          
  [P]  Pause / reprise du dessin en cours      
  [B]  Flou automatique sur les visages        
  [C]  Effacer le dessin                       
  [S]  Sauvegarder le dessin (dessin.png)      
  [H]  Afficher cette aide                     
  [Q] / [ECHAP]  Fermer                       

"""

_prev_poignets: dict = {}
_prev_t = time.time()


def calc_vitesse(md):
    global _prev_t
    side, pos = md["side"], md["wrist"][:2]
    now = time.time()
    dt  = max(0.001, now - _prev_t)
    v   = 0.0
    if side in _prev_poignets:
        v = float(np.linalg.norm(np.array(pos) - np.array(_prev_poignets[side]))) / dt
    _prev_poignets[side] = pos
    _prev_t = now
    return v


def ouvrir_camera():
    cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap = cv2.VideoCapture(CAM_INDEX)
    if not cap.isOpened():
        print("Erreur : webcam introuvable.")
        sys.exit(1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,          CAM_FPS)
    cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
    return cap


def init_cam_virtuelle(w, h):
    try:
        import pyvirtualcam
        cam = pyvirtualcam.Camera(width=w, height=h, fps=30, print_fps=False)
        print(f"[CAM VIRTUELLE] Active : {cam.device}")
        return cam
    except ImportError:
        print("[CAM VIRTUELLE] pyvirtualcam non installé – désactivée.")
    except Exception as e:
        print(f"[CAM VIRTUELLE] Erreur : {e}")
    return None


def main():
    print(AIDE)
    cap = ouvrir_camera()
    w   = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h   = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    det_mains  = HandDetector()
    det_pose   = PoseDetector()
    det_vetems = ClothingDetector()
    reconnaiss = GestureRecognizer()
    hud        = HUD(w, h)
    dessin     = DrawMode(w, h)
    cam_virt   = init_cam_virtuelle(w, h)

    cv2.namedWindow("Suivi corporel V2", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Suivi corporel V2", w, h)

    clothing_cache = []

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        frame = cv2.flip(frame, 1)
        hud.tick_fps()

        poses = det_pose.detect(frame)

        if poses:
            clothing_cache = det_vetems.update(frame, poses)
        else:
            clothing_cache = []

        for pose in poses:
            PoseDetector.draw(frame, pose, flou_tete=MODES["blur"])

        mains  = det_mains.find_hands(frame)
        gestes = []

        for md in mains:
            md["speed"] = calc_vitesse(md)
            md["angle"] = HandDetector.hand_angle(md)
            geste, _    = reconnaiss.recognize(md)
            gestes.append(geste)
            couleur = get_gesture_color(geste)
            draw_hand_skeleton(frame, md, couleur)
            draw_finger_labels(frame, md)
            if MODES["draw"] and not MODES["draw_pause"]:
                dessin.update(md, couleur, md["side"], geste)

        if MODES["draw"]:
            dessin.overlay(frame, 0.82)
            dessin.draw_status(frame)

        hud.draw(frame, mains, gestes, MODES,
                 poses=poses, clothing=clothing_cache)

        cv2.imshow("Suivi corporel V2", frame)

        if cam_virt:
            try:
                cam_virt.send(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                cam_virt.sleep_until_next_frame()
            except Exception:
                pass

        t = cv2.waitKey(1) & 0xFF
        if t in (ord("q"), 27):
            print("Fermeture.")
            break
        elif t == ord("d"):
            actif = dessin.toggle_actif()
            MODES["draw"]       = actif
            MODES["draw_pause"] = False
            print(f"[DESSIN] {'activé' if actif else 'désactivé'}")
        elif t == ord("p"):
            if MODES["draw"]:
                pause = dessin.toggle_pause()
                MODES["draw_pause"] = pause
                print(f"[DESSIN] {'en pause' if pause else 'repris'}")
        elif t == ord("b"):
            MODES["blur"] = not MODES["blur"]
            print(f"[FLOU] {'activé' if MODES['blur'] else 'désactivé'}")
        elif t == ord("c"):
            dessin.clear()
            print("[DESSIN] Effacé.")
        elif t == ord("s"):
            dessin.save()
        elif t == ord("h"):
            print(AIDE)

    cap.release()
    if cam_virt:
        cam_virt.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
