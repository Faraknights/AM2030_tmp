# Utilise une image NVIDIA CUDA avec environnement de développement
FROM nvidia/cuda:12.6.2-devel-ubuntu22.04

# Empêche les prompts interactifs pendant l'installation
ENV DEBIAN_FRONTEND=noninteractive

# Met à jour le système et installe les dépendances système
RUN apt-get update && \
    apt-get install -y \
    git \
    python3 \
    python3-pip \
    python3-dev \
    python3-opencv \
    libglib2.0-0 \
    libopencv-dev \
    libturbojpeg \
    libturbojpeg-dev \
    pkg-config \
    cmake \
    build-essential \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Définit le répertoire de travail
WORKDIR /app

# Copie le fichier requirements.txt pour l'installation des dépendances Python
COPY requirements.txt .

# Met à jour pip et installe les dépendances Python
RUN pip install --upgrade pip && \
    pip install --prefer-binary --no-cache-dir -r requirements.txt

# Copie le reste de l'application dans le conteneur
COPY . .

# Expose le port utilisé par Flask
EXPOSE 5000

# Commande pour lancer l'application Flask
CMD ["python3", "server/app.py"]
