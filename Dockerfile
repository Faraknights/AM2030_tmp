# Define build arguments
ARG USE_CUDA=true
ARG IMAGE="nvidia/cuda:12.5.0-devel-ubuntu22.04"

# Use different base images depending on USE_CUDA
FROM ${IMAGE} 

# Set the argument again (ARGs are not persisted across FROM layers)
ARG USE_CUDA=true

# Install common packages
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y git build-essential \
    python3 python3-pip gcc wget \
    ffmpeg

# Additional OpenCL & CUDA-related packages (only if CUDA is enabled)
RUN if [ "${USE_CUDA}" = "true" ]; then \
    apt-get install -y ocl-icd-opencl-dev opencl-headers clinfo \
    libclblast-dev libopenblas-dev && \
    mkdir -p /etc/OpenCL/vendors && \
    echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd; \
    fi

# Download model
RUN mkdir -p /models && \
    wget https://huggingface.co/mradermacher/Emollama-7b-i1-GGUF/resolve/main/Emollama-7b.i1-Q4_K_M.gguf \
    -O /models/Emollama-7b.i1-Q4_K_M.gguf

COPY . .

# Set GGML_CUDA according to USE_CUDA
ENV GGML_CUDA=${USE_CUDA}

# Common Python dependencies
RUN python3 -m pip install --upgrade pip pytest cmake scikit-build setuptools fastapi uvicorn sse-starlette pydantic-settings starlette-context

# llama-cpp-python with optional CUDA support
RUN if [ "${USE_CUDA}" = "true" ]; then \
    CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python; \
    else \
    pip install llama-cpp-python; \
    fi

# Install project dependencies
RUN python3 -m pip install --break-system-packages -r requirements.txt

CMD ["python3", "server/app.py"]
