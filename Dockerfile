ARG CUDA_IMAGE="12.5.0-devel-ubuntu22.04"
FROM nvidia/cuda:${CUDA_IMAGE}

RUN apt-get update && apt-get upgrade -y \
    && apt-get install -y git build-essential \
    python3 python3-pip gcc wget \
    ocl-icd-opencl-dev opencl-headers clinfo \
    libclblast-dev libopenblas-dev \
    ffmpeg \
    && mkdir -p /etc/OpenCL/vendors && echo "libnvidia-opencl.so.1" > /etc/OpenCL/vendors/nvidia.icd

RUN mkdir -p /models && \
    wget https://huggingface.co/mradermacher/Emollama-7b-i1-GGUF/resolve/main/Emollama-7b.i1-Q4_K_M.gguf \
    -O /models/Emollama-7b.i1-Q4_K_M.gguf

COPY . .

ENV CUDA_DOCKER_ARCH=all
ENV GGML_CUDA=1

# Install depencencies
RUN python3 -m pip install --upgrade pip pytest cmake scikit-build setuptools fastapi uvicorn sse-starlette pydantic-settings starlette-context

# Install llama-cpp-python (build with cuda)
RUN CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python

# Run the server
RUN python3 -m pip install --break-system-packages -r requirements.txt

CMD ["python3", "server/app.py"]
