FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv python3-pip ca-certificates curl ffmpeg fonts-dejavu-core && rm -rf /var/lib/apt/lists/*
WORKDIR /workspace
COPY requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir --upgrade pip && /opt/venv/bin/pip install --no-cache-dir -r /tmp/requirements.txt
ENV PATH="/opt/venv/bin:${PATH}"
CMD ["sleep", "infinity"]
