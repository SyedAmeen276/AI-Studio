import time
import numpy as np
import torch

from kokoro import KPipeline

from app.tts.config import SAMPLE_RATE
from app.tts.pronunciation import PronunciationProcessor

class KokoroEngine:

    def __init__(self, lang_code="a"):
        print("Initializing Kokoro TTS...")

        self.pipeline = KPipeline(lang_code=lang_code)
        self.pronunciation = PronunciationProcessor()

        print("Kokoro initialized.")
        print("MPS available:", torch.backends.mps.is_available())

    def generate(self, text, voice="af_heart", speed=1.0):

        start_time = time.time()
        chunks = []

        processed_text = self.pronunciation.normalize(text)

        generator = self.pipeline(
            processed_text,
            voice=voice,
            speed=speed,
        )

        for index, (graphemes, phonemes, audio) in enumerate(generator):

            if isinstance(audio, torch.Tensor):
                audio = audio.detach().cpu().numpy()

            chunks.append(np.asarray(audio))

            print(f"Generated chunk {index + 1}")

        if not chunks:
            raise RuntimeError("Kokoro generated no audio.")

        final_audio = np.concatenate(chunks)

        duration = len(final_audio) / SAMPLE_RATE
        generation_time = time.time() - start_time

        return {
            "audio": final_audio,
            "duration": duration,
            "generation_time": generation_time,
            "rtf": generation_time / duration if duration else 0,
            "sample_rate": SAMPLE_RATE,
        }