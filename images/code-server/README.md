# Code Server image

This directory builds the managed LabPod Code Server image. It runs as the
workspace owner supplied by LabPod, with code-server started on demand while
the default process remains `sleep infinity`.

The image deliberately has no `/etc/passwd` entry for UID 1000. LabPod mounts a
persistent home directory and injects the workspace owner's account at that
UID; a pre-existing image account would take precedence and direct user data to
a throwaway home directory instead.

The workflow publishes Linux `amd64` to `ghcr.io/labpod/code-server:latest`.
The code-server `.deb` is version-pinned and checksum-verified in the
Dockerfile. `scripts/bump-image-pins.py` updates that pin together with the
other LabPod images that bundle code-server.

## Local build

```sh
podman build -t labpod-code-server:latest images/code-server
```
