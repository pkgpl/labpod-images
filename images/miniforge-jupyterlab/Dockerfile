ARG BASE_IMAGE=docker.io/condaforge/miniforge3:25.3.0-3
FROM ${BASE_IMAGE}

RUN userdel ubuntu 2>/dev/null || true; rm -rf /home/ubuntu
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl \
    && rm -rf /var/lib/apt/lists/* \
    && conda install -y -n base -c conda-forge jupyterlab ipywidgets \
    && conda clean -afy \
    && jupyter lab --version

WORKDIR /work
EXPOSE 8888
ENTRYPOINT ["sleep", "infinity"]
