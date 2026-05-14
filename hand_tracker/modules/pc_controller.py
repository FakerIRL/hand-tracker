import time
import numpy as np



try:
    import pyautogui
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE    = 0
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False
    print("[pc_controller] pyautogui non disponible – contrôle souris désactivé.")

try:
    from ctypes import cast, POINTER
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    _devices   = AudioUtilities.GetSpeakers()
    _interface = _devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    _vol_ctrl  = cast(_interface, POINTER(IAudioEndpointVolume))
    PYCAW_OK   = True
except Exception:
    _vol_ctrl = None
    PYCAW_OK  = False
    print("[pc_controller] pycaw non disponible – contrôle volume désactivé.")

from config import (
    MOUSE_SMOOTH, MOUSE_MARGIN,
    CLICK_COOLDOWN, CLICK_DIST_PX,
    VOL_MIN_PX, VOL_MAX_PX,
    SCROLL_COOLDOWN, SCROLL_DIVISOR,
)


class PCController:
    def __init__(self, frame_w: int, frame_h: int):
        self.fw = frame_w
        self.fh = frame_h
        if PYAUTOGUI_OK:
            self.sw, self.sh = pyautogui.size()
        else:
            self.sw = self.sh = 1080

    
        self._mx = float(self.sw // 2)
        self._my = float(self.sh // 2)

     
        self._last_click  = 0.0
        self._last_scroll = 0.0
        self._last_scroll_y: float | None = None

        
        self._volume = 50



    def move_mouse(self, index_tip: tuple) -> None:
        """Déplace la souris vers la position du bout de l'index."""
        if not PYAUTOGUI_OK:
            return

       
        m   = MOUSE_MARGIN
        nx  = (index_tip[0] / self.fw - m) / (1 - 2 * m)
        ny  = (index_tip[1] / self.fh - m) / (1 - 2 * m)
        nx  = max(0.0, min(1.0, nx))
        ny  = max(0.0, min(1.0, ny))

        tx  = nx * self.sw
        ty  = ny * self.sh

        a       = MOUSE_SMOOTH
        self._mx = a * tx + (1 - a) * self._mx
        self._my = a * ty + (1 - a) * self._my

        pyautogui.moveTo(int(self._mx), int(self._my))

    def check_click(self, thumb_tip: tuple, index_tip: tuple) -> bool:
        """
        Déclenche un clic gauche si le pincement pouce-index est assez serré.
        Retourne True si un clic a eu lieu.
        """
        if not PYAUTOGUI_OK:
            return False

        dist = float(np.linalg.norm(
            np.array(thumb_tip[:2]) - np.array(index_tip[:2])
        ))
        now  = time.time()

        if dist < CLICK_DIST_PX and now - self._last_click > CLICK_COOLDOWN:
            pyautogui.click()
            self._last_click = now
            return True
        return False

  

    def set_volume_from_pinch(self, thumb_tip: tuple, index_tip: tuple) -> int:
        """
        Règle le volume système selon la distance pouce-index.
        Retourne le volume en % (0-100).
        """
        dist = float(np.linalg.norm(
            np.array(thumb_tip[:2]) - np.array(index_tip[:2])
        ))
        vol_f = float(np.interp(dist, [VOL_MIN_PX, VOL_MAX_PX], [0.0, 1.0]))
        vol_f = max(0.0, min(1.0, vol_f))

        if PYCAW_OK and _vol_ctrl is not None:
            try:
                _vol_ctrl.SetMasterVolumeLevelScalar(vol_f, None)
            except Exception:
                pass

        self._volume = int(vol_f * 100)
        return self._volume

    def get_volume(self) -> int:
        return self._volume


    def scroll(self, index_tip_y: float) -> int:
        """
        Fait défiler la page selon le mouvement vertical de l'index.
        Retourne la quantité de défilement (+ = bas, - = haut).
        """
        if not PYAUTOGUI_OK:
            return 0

        if self._last_scroll_y is None:
            self._last_scroll_y = index_tip_y
            return 0

        now = time.time()
        if now - self._last_scroll < SCROLL_COOLDOWN:
            return 0

        dy     = index_tip_y - self._last_scroll_y
        amount = -int(dy / SCROLL_DIVISOR)

        if amount != 0:
            pyautogui.scroll(amount)
            self._last_scroll   = now

        self._last_scroll_y = index_tip_y
        return amount

    def reset_scroll(self) -> None:
        self._last_scroll_y = None



    @staticmethod
    def press_key(key: str) -> None:
        """Appuie sur une touche système."""
        if PYAUTOGUI_OK:
            try:
                pyautogui.press(key)
            except Exception:
                pass

    @staticmethod
    def hotkey(*keys: str) -> None:
        """Combinaison de touches (ex. 'ctrl', 'c')."""
        if PYAUTOGUI_OK:
            try:
                pyautogui.hotkey(*keys)
            except Exception:
                pass
