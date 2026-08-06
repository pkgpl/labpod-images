ARG PYTHON_BASE=ghcr.io/astral-sh/uv:python3.12-bookworm-slim
FROM ${PYTHON_BASE}

ENV UV_SYSTEM_PYTHON=1
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && uv pip install --system --no-cache jupyterlab ipywidgets \
    && jupyter lab --version

WORKDIR /work
EXPOSE 8888
ENTRYPOINT ["sleep", "infinity"]
