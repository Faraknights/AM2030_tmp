FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements to image
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install whisper from GitHub directly
RUN pip install --no-cache-dir git+https://github.com/openai/whisper.git

# Install pexpect
RUN pip install --no-cache-dir pexpect

# Copy project files
COPY . /app
WORKDIR /app

# Optional: wait for Ollama to be ready (avoids timing issues)
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
