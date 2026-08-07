#!/usr/bin/env python3
"""Select the image release matrix affected by a repository change set."""

import argparse
import json
import re
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / ".github" / "image-matrix.json"
FULL_MATRIX_PATHS = {
    ".github/image-matrix.json",
    ".github/workflows/images.yml",
    "scripts/build-input-digest.py",
    "scripts/published-metadata.py",
    "scripts/release-matrix.py",
    "scripts/smoke-image.sh",
}
PACKAGE_DEFAULT_SUFFIX = {
    "code-server": "",
    "pytorch-jupyter": "cu126",
    "tensorflow-jupyter": "cu125",
    "scipy-jupyter": "py312",
    "pytorch-demo": "cpu",
    "miniforge-jupyterlab": "cpu",
    "uv-jupyterlab": "py312",
    "r-ml-jupyterlab": "cpu",
    "rstudio-server": "cpu",
    "llm-huggingface": "cu126",
    "comfyui-stable-diffusion": "cu126",
    "cuda-composite": "cu126",
    "parallel-dev": "cu126",
}
RELEASE_TAG_RE = re.compile(r"^(v\d+)(?:-.+)?$")


def release_prefix(variants):
    prefixes = set()
    for variant in variants:
        match = RELEASE_TAG_RE.fullmatch(variant["tag"])
        if not match:
            raise ValueError(f"invalid immutable release tag: {variant['tag']}")
        prefixes.add(match.group(1))
    if len(prefixes) != 1:
        raise ValueError("image matrix must use one shared vN release prefix")
    return prefixes.pop()


def package_current_tag(name, variants):
    if name not in PACKAGE_DEFAULT_SUFFIX:
        raise ValueError(f"image matrix lacks default-tag metadata for: {name}")
    prefix = release_prefix(variants)
    suffix = PACKAGE_DEFAULT_SUFFIX[name]
    tag = prefix if not suffix else f"{prefix}-{suffix}"
    if not any(item["name"] == name and item["tag"] == tag for item in variants):
        raise ValueError(f"image matrix lacks default variant {name}:{tag}")
    return tag


def load_variants(catalog=CATALOG):
    variants = json.loads(catalog.read_text())["variants"]
    keys = [(variant["name"], variant["tag"]) for variant in variants]
    if len(keys) != len(set(keys)):
        raise ValueError("image matrix contains duplicate name/tag variants")
    unknown_packages = {name for name, _ in keys} - PACKAGE_DEFAULT_SUFFIX.keys()
    if unknown_packages:
        raise ValueError(
            "image matrix lacks default-tag metadata for: "
            + ", ".join(sorted(unknown_packages))
        )
    release_prefix(variants)
    return variants


def build_args(variant):
    name = variant["name"]
    if name in {"pytorch-jupyter", "pytorch-demo"}:
        return "\n".join(
            (
                f"CUDA_BASE_IMAGE={variant['base']}",
                f"TORCH_CUDA={variant['torch_cuda']}",
                f"TORCH_VERSION={variant['torch']}",
                f"TORCHVISION_VERSION={variant['torchvision']}",
            )
        )
    if name == "tensorflow-jupyter":
        return "\n".join(
            (
                f"CUDA_BASE_IMAGE={variant['base']}",
                f"TF_VERSION={variant['tf_version']}",
                f"CUDNN_VERSION={variant['cudnn_version']}",
            )
        )
    if name == "scipy-jupyter":
        return f"BASE_IMAGE={variant['base']}"
    if name == "miniforge-jupyterlab":
        return f"BASE_IMAGE={variant['base']}"
    if name == "uv-jupyterlab":
        return f"PYTHON_BASE={variant['base']}"
    if name in {"r-ml-jupyterlab", "rstudio-server"}:
        return f"BASE_IMAGE={variant['base']}"
    if name == "llm-huggingface":
        return "\n".join(
            (
                f"CUDA_BASE_IMAGE={variant['base']}",
                f"TORCH_CUDA={variant['torch_cuda']}",
                f"TORCH_VERSION={variant['torch']}",
            )
        )
    if name == "comfyui-stable-diffusion":
        return "\n".join(
            (
                f"CUDA_BASE_IMAGE={variant['base']}",
                f"TORCH_CUDA={variant['torch_cuda']}",
                f"TORCH_VERSION={variant['torch']}",
                f"TORCHVISION_VERSION={variant['torchvision']}",
                f"TORCHAUDIO_VERSION={variant['torchaudio']}",
                f"COMFYUI_REF={variant['comfyui_ref']}",
            )
        )
    if name in {"cuda-composite", "parallel-dev"}:
        return f"CUDA_BASE_IMAGE={variant['base']}"
    return ""


def workflow_variant(variant):
    name = variant["name"]
    args = build_args(variant)
    return {
        "name": name,
        "repository": f"ghcr.io/labpod/{name}",
        "tag": variant["tag"],
        "context": f"images/{name}",
        "dockerfile": f"images/{name}/Dockerfile",
        "kind": name,
        "build_args": args,
        "build_input_args": args,
    }


def select_variant_names(paths, variants, force_all=False):
    ordered_names = list(dict.fromkeys(variant["name"] for variant in variants))
    if force_all:
        return ordered_names

    normalized = set()
    for path in paths:
        path = path.strip()
        if not path:
            continue
        if path.startswith("./"):
            path = path[2:]
        normalized.add(path)
    if normalized & FULL_MATRIX_PATHS:
        return ordered_names

    known_names = set(ordered_names)
    selected = set()
    for path in normalized:
        parts = PurePosixPath(path).parts
        if len(parts) < 3 or parts[0] != "images":
            continue
        name = parts[1]
        if name not in known_names:
            raise ValueError(f"image path has no release-matrix entry: {path}")
        if parts[-1] == "README.md":
            continue
        selected.add(name)
    return [name for name in ordered_names if name in selected]


def release_scope(
    paths=(), force_all=False, force_all_if_changed=False, catalog=CATALOG
):
    variants = load_variants(catalog)
    names = select_variant_names(paths, variants, force_all=force_all)
    if force_all_if_changed and names:
        names = select_variant_names((), variants, force_all=True)
    selected = [variant for variant in variants if variant["name"] in names]
    variant_matrix = {"include": [workflow_variant(item) for item in selected]}
    package_matrix = {
        "include": [
            {
                "name": name,
                "repository": f"ghcr.io/labpod/{name}",
                "current_tag": package_current_tag(name, variants),
            }
            for name in names
        ]
    }
    return {
        "release_required": "true" if selected else "false",
        "variant_matrix": variant_matrix,
        "package_matrix": package_matrix,
    }


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="select every variant")
    group.add_argument("--paths-file", type=Path, help="newline-delimited changed paths")
    group.add_argument(
        "--all-if-paths-file",
        type=Path,
        help="select every variant when the changed paths affect a release",
    )
    args = parser.parse_args()

    paths_file = args.paths_file or args.all_if_paths_file
    paths = () if args.all else paths_file.read_text().splitlines()
    scope = release_scope(
        paths,
        force_all=args.all,
        force_all_if_changed=args.all_if_paths_file is not None,
    )
    print(f"release_required={scope['release_required']}")
    print("variant_matrix=" + json.dumps(scope["variant_matrix"], separators=(",", ":")))
    print("package_matrix=" + json.dumps(scope["package_matrix"], separators=(",", ":")))


if __name__ == "__main__":
    main()
