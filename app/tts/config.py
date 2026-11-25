from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0
SAMPLE_RATE = 24000

AUDIO_OUTPUT_DIR = PROJECT_ROOT / "output" / "audio"

# American English voices for initial comparison
SUPPORTED_VOICES = {
    "af_heart": "Female - Heart",
    "af_bella": "Female - Bella",
    "af_nicole": "Female - Nicole",
    "am_michael": "Male - Michael",
    "am_fenrir": "Male - Fenrir",
}