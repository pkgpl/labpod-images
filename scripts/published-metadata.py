#!/usr/bin/env python3
"""Generate the canonical LabPod bundle-facing image metadata catalog."""

import argparse
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def load_module(filename, name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


MATRIX = load_module("release-matrix.py", "release_matrix")
DIGEST = load_module("build-input-digest.py", "build_input_digest")


def published_metadata():
    variants = MATRIX.load_variants()
    names = list(dict.fromkeys(item["name"] for item in variants))
    images = []
    for name in names:
        image_variants = [item for item in variants if item["name"] == name]
        default_tag = MATRIX.package_current_tag(name, variants)
        default = next(item for item in image_variants if item["tag"] == default_tag)
        context = ROOT / "images" / name
        dockerfile = context / "Dockerfile"

        generated = []
        variant_build_args = {}
        for item in image_variants:
            args = DIGEST.parse_build_args(MATRIX.build_args(item))
            ref = f"ghcr.io/labpod/{name}:{item['tag']}"
            definition_digest = DIGEST.build_input_digest(context, dockerfile, args)
            generated.append(
                {
                    "ref": ref,
                    "definition_digest": definition_digest,
                    "build_args": args,
                }
            )
            variant_build_args[item["tag"]] = args

        default_ref = f"ghcr.io/labpod/{name}:{default_tag}"
        default_generated = next(item for item in generated if item["ref"] == default_ref)
        images.append(
            {
                "name": name,
                "dockerfile": f"images/{name}/Dockerfile",
                "build_args": DIGEST.parse_build_args(MATRIX.build_args(default)),
                "variant_build_args": variant_build_args,
                "published": {
                    "ref": default_generated["ref"],
                    "definition_digest": default_generated["definition_digest"],
                    "variants": [
                        item for item in generated if item["ref"] != default_ref
                    ],
                },
            }
        )
    return {
        "schema_version": 1,
        "digest_algorithm": "labpod.build-input.v1",
        "image_label": "ai.labpod.image.build-input-digest",
        "images": images,
    }


def rendered():
    return json.dumps(published_metadata(), indent=2, sort_keys=False) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = ROOT / "published-images.json"
    expected = rendered()
    if args.write:
        target.write_text(expected)
        return
    if args.check:
        if not target.exists() or target.read_text() != expected:
            raise SystemExit("published-images.json is stale; run scripts/published-metadata.py --write")
        return
    print(expected, end="")


if __name__ == "__main__":
    main()
