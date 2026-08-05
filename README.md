# LabPod Managed Workspace Images

This repository is the public source and publishing home for LabPod's managed
workspace container images. The images are built for Podman workspaces and are
designed to run as the LabPod workspace owner without requiring a fixed runtime
user.

## Images

| Image | Purpose | Example |
|---|---|---|
| `code-server` | Browser-based VS Code workspace | `ghcr.io/labpod/code-server:latest` |
| `pytorch-jupyter` | PyTorch, JupyterLab, TensorBoard, and code-server | `ghcr.io/labpod/pytorch-jupyter:cu126` |
| `tensorflow-jupyter` | TensorFlow, JupyterLab, TensorBoard, and code-server | `ghcr.io/labpod/tensorflow-jupyter:cu125` |
| `scipy-jupyter` | CPU data-science and JupyterLab environment | `ghcr.io/labpod/scipy-jupyter:py312` |
| `pytorch-demo` | LabPod demonstration workspace | `ghcr.io/labpod/pytorch-demo:cpu` |

Pull an image with Podman, for example:

```bash
podman pull ghcr.io/labpod/pytorch-jupyter:cu126
```

## Tags and reproducibility

Tags such as `cu121`, `cu126`, `cu129`, `cu125`, `py312`, and `cpu` describe
runtime compatibility channels. They may be rebuilt to pick up security and
dependency updates. Pin an image digest when an exact, reproducible image is
required.

The host supplies the NVIDIA driver for GPU images. Select a CUDA channel that
is compatible with both the host driver and GPU architecture; see each image's
README for its supported matrix.

## Relationship to LabPod

These packages are maintained independently from the LabPod server release
channel. LabPod server releases, portable CLI binaries, and the matching agent
skill are published at [LabPod releases](https://github.com/LabPod/labpod/releases).
Product documentation is available at [docs.labpod.ai](https://docs.labpod.ai).
