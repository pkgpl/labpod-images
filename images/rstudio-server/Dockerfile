# RStudio Server workspace on the CPU rocker/rstudio base. Same stay-alive
# shape as the other LabPod images: PID 1 is sleep-infinity, LabPod starts
# rserver on demand via `podman exec`, and `podman run --init` reaps zombies.
#
# LabPod runs the container rootless as the workspace owner with
# --cap-drop=ALL / --security-opt no-new-privileges / --userns=keep-id.
# RStudio Server's default root+PAM multi-user model cannot start under that,
# so labpod-rstudio runs the single-user, auth-none pattern HPC sites use under
# Apptainer: rserver as the current user, no PAM, with all runtime state under
# a writable per-run temp dir. LabPod's reverse proxy is the access boundary.
ARG BASE_IMAGE=docker.io/rocker/rstudio:4.4.1
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        openssl \
        python3 \
        python3-venv \
        tmux \
        vim \
    && rm -rf /var/lib/apt/lists/*

# The CPU RStudio base does not carry rocker/ml's advertised data-science
# packages. Install and attach each one so a missing shared library fails the
# image build rather than a researcher's first RStudio session.
RUN Rscript -e 'pkgs <- c("tidyverse", "data.table", "reticulate"); \
      install.packages(pkgs, Ncpus = max(1L, parallel::detectCores(), na.rm = TRUE)); \
      missing <- setdiff(pkgs, rownames(installed.packages())); \
      if (length(missing)) stop("failed to install: ", paste(missing, collapse = ", "))' \
    && Rscript -e 'pkgs <- c("tidyverse", "data.table", "reticulate"); \
      ok <- vapply(pkgs, function(p) tryCatch({ \
        library(p, character.only = TRUE); TRUE \
      }, error = function(e) { message(conditionMessage(e)); FALSE }), logical(1)); \
      if (any(!ok)) stop("failed to load: ", paste(pkgs[!ok], collapse = ", "))'

# Keep the historical UID 1000 cleanup for compatibility with older LabPod
# releases. Current LabPod can run the baked rocker account too by mapping the
# host owner to a free image-local uid/gid before injecting persistent HOME.
RUN userdel rstudio 2>/dev/null || true; rm -rf /home/rstudio

# Rootless rserver launcher. The launcher passes --www-port and
# --www-root-path as extra args; everything that rserver writes to by default
# is redirected under a writable per-user runtime dir.
RUN cat > /usr/local/bin/labpod-rstudio <<'EOF' \
    && chmod 0755 /usr/local/bin/labpod-rstudio
#!/usr/bin/env bash
set -euo pipefail

# Resolve USER from the configured numeric container identity so the wrapper
# remains correct across both legacy UID cleanup and current keep-id remapping.
USER="$(id -un)"
export USER

runtime_dir="${XDG_RUNTIME_DIR:-/tmp}/labpod-rstudio-$(id -u)"
mkdir -p "$runtime_dir/run" "$runtime_dir/db"
chmod 700 "$runtime_dir"

db_conf="$runtime_dir/database.conf"
printf 'provider=sqlite\ndirectory=%s/db\n' "$runtime_dir" > "$db_conf"

cookie_key="$runtime_dir/secure-cookie-key"
if [ ! -f "$cookie_key" ]; then
  openssl rand -hex 32 > "$cookie_key"
  chmod 600 "$cookie_key"
fi

exec /usr/lib/rstudio-server/bin/rserver \
  --server-user="$(id -un)" \
  --server-daemonize=0 \
  --server-data-dir="$runtime_dir/run" \
  --server-pid-file="$runtime_dir/rstudio-server.pid" \
  --auth-none=1 \
  --www-address=0.0.0.0 \
  --secure-cookie-key-file="$cookie_key" \
  --database-config-file="$db_conf" \
  --rsession-which-r="$(command -v R)" \
  "$@"
EOF

WORKDIR /work
EXPOSE 8787

ENTRYPOINT ["sleep", "infinity"]
