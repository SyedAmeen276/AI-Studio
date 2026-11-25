import os
import time
import numpy as np
import soundfile as sf
import torch

from kokoro import KPipeline

TEXT = """
Welcome to AI Content Studio.

Today we are learning how Docker works internally.

Docker allows applications to run in isolated environments
using containers.

Let's understand the architecture step by step.
"""

VOICE = "af_heart"
SAMPLE_RATE = 24000

OUTPUT_FILE = "output/audio/kokoro_test.wav"


def main():
    os.makedirs("output/audio", exist_ok=True)

    print("Initializing Kokoro...")
    print("MPS available:", torch.backends.mps.is_available())

    start_time = time.time()

    pipeline = KPipeline(lang_code="a")

    print("Generating speech...")

    generator = pipeline(
        TEXT,
        voice=VOICE,
        speed=1.0,
        split_pattern=r"\n+"
    )

    chunks = []

    for index, (graphemes, phonemes, audio) in enumerate(generator):
        print(f"Generated chunk: {index + 1}")
        print("Text:", graphemes)

        if isinstance(audio, torch.Tensor):
            audio = audio.detach().cpu().numpy()

        chunks.append(np.asarray(audio))

    if not chunks:
        raise RuntimeError("No audio was generated.")

    final_audio = np.concatenate(chunks)

    sf.write(OUTPUT_FILE, final_audio, SAMPLE_RATE)

    duration = len(final_audio) / SAMPLE_RATE

    print("\nTTS generation completed!")
    print("Output:", OUTPUT_FILE)
    print("Duration:", round(duration, 2), "seconds")
    print("Generation time:", round(time.time() - start_time, 2), "seconds")


if __name__ == "__main__":
    main()