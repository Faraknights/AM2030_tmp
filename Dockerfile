# Base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential git ffmpeg curl && \
    apt-get clean

# Set workdir
WORKDIR /app

# Copy only requirements first to leverage caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Expose port
EXPOSE 5000

# Start the app
CMD ["python3", "server/app.py"]
