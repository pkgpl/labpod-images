ARG CUDA_BASE_IMAGE=docker.io/nvidia/cuda:12.1.1-devel-ubuntu22.04
FROM ${CUDA_BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
ARG CODE_SERVER_VERSION=4.118.0
ARG CODE_SERVER_SHA256_AMD64=fe2988f313c9047c1e1ccccee10ad8ccf2813b66a02c146e7d4fd2a3f7e2dc81
ARG CODE_SERVER_SHA256_ARM64=81fa5486a674428507cfb68025764646bdb99c345b8ca798fd94a13ea056eeb3

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential gfortran clang clangd cmake gdb libopenmpi-dev \
        openmpi-bin libomp-dev bash ca-certificates curl git htop iproute2 jq \
        less nano openssh-client python3 python3-pip python3-venv rsync tmux \
        tree unzip vim wget \
    && rm -rf /var/lib/apt/lists/*

RUN NSIGHT_VER="$(echo "${CUDA_VERSION}" | cut -d. -f1,2 | tr '.' '-')" \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        "cuda-nsight-systems-${NSIGHT_VER}" "cuda-nsight-compute-${NSIGHT_VER}" \
    && rm -rf /var/lib/apt/lists/*

# code-server is MIT licensed and redistributable. Microsoft `code serve-web`
# intentionally stays out of published images and remains a local/EULA path.
RUN arch="$(dpkg --print-architecture)" \
    && case "$arch" in \
        amd64) expected="$CODE_SERVER_SHA256_AMD64" ;; \
        arm64) expected="$CODE_SERVER_SHA256_ARM64" ;; \
        *) echo "unsupported architecture: $arch" >&2; exit 1 ;; \
    esac \
    && artifact="code-server_${CODE_SERVER_VERSION}_${arch}.deb" \
    && curl -fsSL "https://github.com/coder/code-server/releases/download/v${CODE_SERVER_VERSION}/${artifact}" -o "/tmp/${artifact}" \
    && echo "${expected}  /tmp/${artifact}" | sha256sum -c - \
    && apt-get update \
    && apt-get install -y --no-install-recommends "/tmp/${artifact}" \
    && rm -f "/tmp/${artifact}" \
    && rm -rf /var/lib/apt/lists/* \
    && code-server --version

WORKDIR /work
EXPOSE 8080
ENTRYPOINT ["sleep", "infinity"]
