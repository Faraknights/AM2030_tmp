FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    cmake \
    curl \
    wget \
    python3-dev \
    libcurl4-openssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# llama.cpp
WORKDIR /opt
RUN git clone https://github.com/ggerganov/llama.cpp.git
WORKDIR /opt/llama.cpp
RUN mkdir build && cd build && cmake .. && make -j

# emollama quantized
RUN mkdir -p /models
WORKDIR /models
RUN wget https://huggingface.co/mradermacher/Emollama-7b-i1-GGUF/resolve/main/Emollama-7b.i1-Q4_K_M.gguf -O Emollama-7b.i1-Q4_K_M.gguf

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "server/app.py"]
