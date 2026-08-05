#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 <image-ref> <code-server|pytorch-jupyter|tensorflow-jupyter|scipy-jupyter|pytorch-demo>" >&2
  exit 2
}

[[ $# -eq 2 ]] || usage
image_ref=$1
image_kind=$2
engine=${CONTAINER_ENGINE:-docker}

case "$image_kind" in
  code-server|pytorch-jupyter|tensorflow-jupyter|scipy-jupyter|pytorch-demo) ;;
  *) usage ;;
esac

fail() {
  echo "smoke failure: $*" >&2
  exit 1
}

container_id=""
cleanup() {
  if [[ -n "$container_id" ]]; then
    "$engine" rm -f "$container_id" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

[[ $("$engine" image inspect --format '{{.Architecture}}' "$image_ref") == amd64 ]] \
  || fail "published image is not linux/amd64"
[[ -z $("$engine" image inspect --format '{{.Config.User}}' "$image_ref") ]] \
  || fail "image bakes a runtime USER"
[[ $("$engine" image inspect --format '{{.Config.WorkingDir}}' "$image_ref") == /work ]] \
  || fail "image WORKDIR is not /work"
[[ $("$engine" image inspect --format '{{json .Config.Entrypoint}}' "$image_ref") == '["sleep","infinity"]' ]] \
  || fail "image entrypoint is not sleep infinity"

container_id=$("$engine" run -d "$image_ref")
for _ in $(seq 1 10); do
  [[ $("$engine" inspect --format '{{.State.Running}}' "$container_id") == true ]] && break
  sleep 1
done
[[ $("$engine" inspect --format '{{.State.Running}}' "$container_id") == true ]] \
  || fail "default container process did not stay running"

probe_http() {
  local name=$1
  local port=$2
  local path=$3
  local command=$4
  local log="/tmp/labpod-smoke-${name}.log"

  "$engine" exec "$container_id" sh -c "$command >'$log' 2>&1 &"
  for _ in $(seq 1 45); do
    if "$engine" exec "$container_id" curl -fsS "http://127.0.0.1:${port}${path}" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  "$engine" exec "$container_id" sh -c "cat '$log'" >&2 || true
  fail "$name did not answer HTTP on port $port"
}

case "$image_kind" in
  code-server)
    "$engine" exec "$container_id" code-server --version
    probe_http code-server 8080 / \
      "code-server --bind-addr 127.0.0.1:8080 --auth none /work"
    ;;
  pytorch-jupyter)
    "$engine" exec "$container_id" python3 -c \
      'import torch, torchvision; x=torch.tensor([1.0, 2.0]); assert torch.dot(x, x).item() == 5.0'
    "$engine" exec "$container_id" code-server --version
    probe_http jupyter 8888 /lab \
      "jupyter lab --allow-root --no-browser --ip=127.0.0.1 --port=8888 --ServerApp.token='' --ServerApp.password=''"
    probe_http tensorboard 6006 / \
      "tensorboard --host 127.0.0.1 --port 6006 --logdir /tmp/tensorboard"
    probe_http code-server 8080 / \
      "code-server --bind-addr 127.0.0.1:8080 --auth none /work"
    ;;
  tensorflow-jupyter)
    "$engine" exec -e CUDA_VISIBLE_DEVICES=-1 "$container_id" python3 -c \
      'import tensorflow as tf; x=tf.ones((1, 4, 4, 1)); y=tf.keras.layers.Conv2D(1, 2)(x); assert tuple(y.shape) == (1, 3, 3, 1)'
    "$engine" exec "$container_id" code-server --version
    probe_http jupyter 8888 /lab \
      "jupyter lab --allow-root --no-browser --ip=127.0.0.1 --port=8888 --ServerApp.token='' --ServerApp.password=''"
    probe_http tensorboard 6006 / \
      "tensorboard --host 127.0.0.1 --port 6006 --logdir /tmp/tensorboard"
    probe_http code-server 8080 / \
      "code-server --bind-addr 127.0.0.1:8080 --auth none /work"
    ;;
  scipy-jupyter)
    "$engine" exec "$container_id" python3 -c \
      'import bokeh, matplotlib, numpy, pandas, scipy, seaborn, sklearn; from scipy.linalg import solve; assert solve([[2.0]], [4.0])[0] == 2.0'
    probe_http jupyter 8888 /lab \
      "jupyter lab --allow-root --no-browser --ip=127.0.0.1 --port=8888 --ServerApp.token='' --ServerApp.password=''"
    ;;
  pytorch-demo)
    "$engine" exec "$container_id" python3 -c \
      'import aim, mlflow, torch, torchvision; x=torch.tensor([1.0, 2.0]); assert torch.dot(x, x).item() == 5.0'
    "$engine" exec "$container_id" code-server --version
    "$engine" exec "$container_id" ttyd --version
    probe_http jupyter 8888 /lab \
      "jupyter lab --allow-root --no-browser --ip=127.0.0.1 --port=8888 --ServerApp.token='' --ServerApp.password=''"
    probe_http tensorboard 6006 / \
      "tensorboard --host 127.0.0.1 --port 6006 --logdir /tmp/tensorboard"
    probe_http code-server 8080 / \
      "code-server --bind-addr 127.0.0.1:8080 --auth none /work"
    probe_http ttyd 7681 / \
      "ttyd -i 127.0.0.1 -p 7681 sh"
    ;;
esac

echo "smoke passed: $image_ref ($image_kind)"
