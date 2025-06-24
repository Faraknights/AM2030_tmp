#!/bin/sh

# Optional: wait until Ollama is up (port 11434)
echo "Waiting for Ollama to start..."
while ! nc -z ollama 11434; do
  sleep 1
done

echo "Ollama is up. Running setup..."

python3 server/modules/generating_prompts.py

echo "Starting FastAPI app..."
exec python3 server/app.py
