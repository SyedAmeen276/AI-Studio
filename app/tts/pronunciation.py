import json
import re
from pathlib import Path


DICTIONARY_PATH = Path(__file__).with_name("pronunciation.json")


class PronunciationProcessor:

    def __init__(self, dictionary_path=DICTIONARY_PATH):

        self.dictionary_path = Path(dictionary_path)

        with self.dictionary_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            self.dictionary = json.load(file)

        # Longer phrases must be replaced before shorter terms.
        self.patterns = sorted(
            self.dictionary.items(),
            key=lambda item: len(item[0]),
            reverse=True
        )

    def normalize(self, text):

        if not isinstance(text, str):
            raise TypeError("Input text must be a string.")

        result = text

        for original, replacement in self.patterns:

            pattern = (
                r"(?<![A-Za-z0-9])"
                + re.escape(original)
                + r"(?![A-Za-z0-9])"
            )

            result = re.sub(
                pattern,
                lambda _: replacement,
                result,
                flags=re.IGNORECASE
            )

        return result