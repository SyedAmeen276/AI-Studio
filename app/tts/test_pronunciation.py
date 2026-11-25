from app.tts.pronunciation import PronunciationProcessor


processor = PronunciationProcessor()

sample = """
C++ is a programming language.

We use TCP/IP for communication.

Docker exposes a REST API.

The application returns JSON.

Kubernetes manages containers.

GPU and CPU are different processing units.

We use SQL and NoSQL databases.
"""

result = processor.normalize(sample)

print("ORIGINAL TEXT")
print("================")
print(sample)

print("\nNORMALIZED TEXT")
print("================")
print(result)