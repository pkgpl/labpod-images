ARG CUDA_BASE_IMAGE=docker.io/nvidia/cuda:12.1.1-runtime-ubuntu22.04
FROM ${CUDA_BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ARG COMFYUI_REF=v0.3.51
ARG TORCH_CUDA=cu121
ARG TORCH_VERSION=2.5.1
ARG TORCHVISION_VERSION=0.20.1
ARG TORCHAUDIO_VERSION=2.5.1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash ca-certificates curl git python3 python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m pip install --no-cache-dir uv

RUN git clone --filter=blob:none https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI \
    && git -C /opt/ComfyUI checkout "${COMFYUI_REF}" \
    && uv pip install --system --no-cache \
        --index-url "https://download.pytorch.org/whl/${TORCH_CUDA}" \
        "torch==${TORCH_VERSION}" \
        "torchvision==${TORCHVISION_VERSION}" \
        "torchaudio==${TORCHAUDIO_VERSION}" \
    && uv pip install --system --no-cache -r /opt/ComfyUI/requirements.txt \
    && cd /opt/ComfyUI \
    && python3 -c 'import torch; import folder_paths'

RUN printf '%s\n' \
        '#!/usr/bin/env bash' \
        'set -euo pipefail' \
        'mkdir -p /work/comfyui' \
        'cd /opt/ComfyUI' \
        'exec python3 main.py --base-directory /work/comfyui "$@"' \
        > /usr/local/bin/comfyui \
    && chmod 0755 /usr/local/bin/comfyui

WORKDIR /work
EXPOSE 8188
ENTRYPOINT ["sleep", "infinity"]
