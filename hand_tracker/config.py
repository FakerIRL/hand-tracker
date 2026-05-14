
CAM_INDEX       = 0
CAM_WIDTH       = 1280
CAM_HEIGHT      = 720
CAM_FPS         = 60


MAX_HANDS           = 2
DETECTION_CONF      = 0.75
TRACKING_CONF       = 0.60


DIST_COEFF          = 6500 
DIST_PROCHE         = 30     
DIST_LOIN           = 65    


TRAIL_MAX_LEN       = 25
TRAIL_DURATION      = 0.45 


MAX_PARTICLES       = 300
PARTICLES_PER_FRAME = 2


MOUSE_SMOOTH        = 0.25  
MOUSE_MARGIN        = 0.12  
CLICK_COOLDOWN      = 0.45  
CLICK_DIST_PX       = 38     

VOL_MIN_PX          = 25
VOL_MAX_PX          = 210

SCROLL_COOLDOWN     = 0.04
SCROLL_DIVISOR      = 8

SWIPE_WINDOW        = 0.45   # secondes
SWIPE_THRESHOLD_PX  = 60

C_TEAL      = (180, 220, 0)
C_CYAN      = (255, 220, 0)
C_GREEN     = (100, 255, 0)
C_ORANGE    = (0,   140, 255)
C_PINK      = (200,  80, 255)
C_WHITE     = (240, 240, 240)
C_DIM       = (70,   70,  70)
C_RED       = (0,    60, 230)
C_YELLOW    = (0,   230, 230)
C_PURPLE    = (230,  80, 150)

GESTURE_COLORS = {
    "MAIN OUVERTE":     (150, 255,  60),
    "POING":            (0,    50, 220),
    "POUCE LEVE":       (0,   230, 230),
    "PEACE":            (230, 130,   0),
    "POINTAGE":         (0,   255, 255),
    "DOIGT D HONNEUR":  (0,    60, 255),
    "OK":               (0,   200, 255),
    "SWIPE":            (200, 255,   0),
    "default":          (120, 200, 255),
}

FINGER_NAMES   = ["thumb", "index", "middle", "ring", "pinky"]
FINGER_TIP_IDS = {"thumb": 4, "index": 8, "middle": 12, "ring": 16, "pinky": 20}
FINGER_PIP_IDS = {"thumb": 3, "index": 6, "middle": 10, "ring": 14, "pinky": 18}
FINGER_MCP_IDS = {"thumb": 2, "index": 5, "middle": 9,  "ring": 13, "pinky": 17}


SKELETON_CHAINS = [
    [0, 1, 2, 3, 4],      
    [0, 5, 6, 7, 8],       
    [0, 9, 10, 11, 12],    
    [0, 13, 14, 15, 16],    
    [0, 17, 18, 19, 20],   
    [5, 9, 13, 17, 0],      
]
