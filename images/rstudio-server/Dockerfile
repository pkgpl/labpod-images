ARG BASE_IMAGE=docker.io/rocker/rstudio:4.4.1
FROM ${BASE_IMAGE}

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl openssl tmux vim \
    && rm -rf /var/lib/apt/lists/*
RUN userdel rstudio 2>/dev/null || true; rm -rf /home/rstudio

RUN cat > /usr/local/bin/labpod-rstudio <<'EOF' \
    && chmod 0755 /usr/local/bin/labpod-rstudio
#!/usr/bin/env bash
set -euo pipefail
USER="$(id -un)"
export USER
runtime_dir="${XDG_RUNTIME_DIR:-/tmp}/labpod-rstudio-$(id -u)"
mkdir -p "$runtime_dir/run" "$runtime_dir/db"
chmod 700 "$runtime_dir"
printf 'provider=sqlite\ndirectory=%s/db\n' "$runtime_dir" > "$runtime_dir/database.conf"
if [[ ! -f "$runtime_dir/secure-cookie-key" ]]; then
  openssl rand -hex 32 > "$runtime_dir/secure-cookie-key"
  chmod 600 "$runtime_dir/secure-cookie-key"
fi
exec /usr/lib/rstudio-server/bin/rserver \
  --server-user="$(id -un)" \
  --server-daemonize=0 \
  --server-data-dir="$runtime_dir/run" \
  --server-pid-file="$runtime_dir/rstudio-server.pid" \
  --auth-none=1 \
  --www-address=0.0.0.0 \
  --secure-cookie-key-file="$runtime_dir/secure-cookie-key" \
  --database-config-file="$runtime_dir/database.conf" \
  --rsession-which-r="$(command -v R)" \
  "$@"
EOF

WORKDIR /work
EXPOSE 8787
ENTRYPOINT ["sleep", "infinity"]
