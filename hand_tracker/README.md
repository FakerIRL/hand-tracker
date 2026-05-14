# Hand Tracker V2

Suivi en temps réel du corps, des mains et du visage via webcam.

---

## Installation

```bash
python -m pip install opencv-python mediapipe numpy pyautogui pyvirtualcam
python main.py
```

Les modèles MediaPipe se téléchargent automatiquement au premier lancement.

---

## Raccourcis aussi donner au lancement du script

| Touche | Action |
|--------|--------|
| D | Dessin dans l'air |
| P | Pause / reprise du dessin |
| B | Flou sur les visages |
| C | Effacer le dessin |
| S | Sauvegarder le dessin |
| Q / ECHAP | Fermer |

---

## Fonctionnalités

- Squelette corps complet (MediaPipe Pose)
- Suivi des mains et doigts (MediaPipe Hands)
- Multi-personnes jusqu'à 4 (ENTITE 1 à 4)
- Détection lunettes, casquette, couleur des vêtements
- Flou elliptique sur les visages
- Dessin dans l'air avec pause/reprise
- Caméra virtuelle compatible Discord / OBS

---

## Structure

```
hand_tracker/
├── main.py
├── config.py
└── modules/
    ├── hand_detector.py
    ├── pose_detector.py
    ├── clothing_detector.py
    ├── gesture_recognizer.py
    ├── draw_mode.py
    ├── visual_effects.py
    └── hud.py
```