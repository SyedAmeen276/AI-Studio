from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

VIDEO_OUTPUT_DIR = PROJECT_ROOT / "output" / "videos"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30

BACKGROUND_COLOR = "#101827"
TITLE_COLOR = "white"
SUBTITLE_COLOR = "#AAB8CC"

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"