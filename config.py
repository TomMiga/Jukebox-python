import os

# Automaticky použije složku, ve které program leží (funguje na D:\jukebox, Macu i RPi)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MUSIC_DIR = os.path.join(BASE_DIR, "music")
VIDEOS_DIR = os.path.join(BASE_DIR, "videos")
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "library.db")
COVERS_DIR = os.path.join(DATA_DIR, "covers")

# Discogs API token pro stahování raritních a českých obalů
DISCOGS_TOKEN = ""  # Sem vlož svůj osobní token z Discogs (Settings -> Developers)
os.makedirs(MUSIC_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COVERS_DIR, exist_ok=True)

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FULLSCREEN = False
FPS = 30

# Retro Maxi Music Box paleta
COLOR_BG = (18, 8, 8)
COLOR_SIDE_STRIP = (95, 18, 22)
COLOR_SIDE_TEXT = (195, 65, 55)

COLOR_PANEL_YELLOW = (242, 206, 48)
COLOR_PANEL_YELLOW_LIGHT = (255, 240, 120)
COLOR_PANEL_YELLOW_DARK = (145, 115, 10)

COLOR_SELECT_BG = (10, 20, 95)
COLOR_SELECT_TEXT = (255, 255, 255)
COLOR_TEXT_DARK = (15, 15, 15)
COLOR_TEXT_RED = (200, 20, 20)

COLOR_BTN_PINK = (230, 55, 135)
COLOR_BTN_PINK_LIGHT = (255, 145, 195)
COLOR_BTN_PINK_DARK = (130, 15, 70)
COLOR_ARROW_CYAN = (45, 195, 235)

COLOR_BOX_RED = (210, 18, 18)
COLOR_BOX_RED_LIGHT = (255, 95, 95)
COLOR_BOX_RED_DARK = (115, 5, 5)

COLOR_BOX_GREEN = (25, 155, 55)
COLOR_BOX_GREEN_LIGHT = (95, 225, 120)
COLOR_BOX_GREEN_DARK = (10, 80, 25)
COLOR_QUEUE_BG = (215, 235, 215)