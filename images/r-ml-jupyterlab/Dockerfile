ARG BASE_IMAGE=docker.io/rocker/r-ver:4.4.1
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:${PATH} \
    RETICULATE_PYTHON=/opt/venv/bin/python

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates curl git libzmq5 python3 python3-pip python3-venv tmux vim \
    && rm -rf /var/lib/apt/lists/*
RUN userdel rstudio 2>/dev/null || true; rm -rf /home/rstudio

RUN python3 -m venv "$VIRTUAL_ENV" \
    && "$VIRTUAL_ENV/bin/pip" install --no-cache-dir \
        jupyterlab ipykernel ipywidgets jupyter-resource-usage numpy tensorboard \
    && Rscript -e 'pkgs <- c("tidyverse", "tidymodels", "caret", "xgboost", "randomForest", "glmnet", "data.table", "reticulate", "IRkernel"); install.packages(pkgs, Ncpus=max(1L, parallel::detectCores(), na.rm=TRUE)); missing <- setdiff(pkgs, rownames(installed.packages())); if (length(missing)) stop("failed to install: ", paste(missing, collapse=", "))' \
    && Rscript -e 'IRkernel::installspec(user=FALSE)' \
    && jupyter kernelspec list

WORKDIR /work
EXPOSE 8888 6006
ENTRYPOINT ["sleep", "infinity"]
