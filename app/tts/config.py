from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_VOICE = "af_heart"
DEFAULT_SPEED = 1.0
SAMPLE_RATE = 24000

AUDIO_OUTPUT_DIR = PROJECT_ROOT / "output" / "audio"

SUPPORTED_VOICES = [
    "af_heart",
    "af_bella",
    "af_nicole",
    "am_adam",
    "am_michael",
]