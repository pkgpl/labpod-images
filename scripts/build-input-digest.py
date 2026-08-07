#!/usr/bin/env python3
"""Compute LabPod's offline-reproducible build-input digest (v1)."""

import argparse
import hashlib
import os
import re
import struct
from pathlib import Path


MAGIC = b"labpod.build-input.v1\0"
VARIABLE = re.compile(r"\$(?:\{([A-Za-z_][A-Za-z0-9_]*)\}|([A-Za-z_][A-Za-z0-9_]*))")


def parse_build_args(value):
    result = {}
    for line in value.splitlines():
        line = line.strip()
        if not line:
            continue
        if "=" not in line:
            raise ValueError(f"build argument has no '=': {line}")
        name, item = line.split("=", 1)
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            raise ValueError(f"invalid build argument name: {name}")
        result[name] = item
    return dict(sorted(result.items()))


def frame(kind, key, value):
    fields = (kind.encode(), key.encode(), value)
    return b"".join(struct.pack(">Q", len(field)) + field for field in fields)


def logical_lines(text):
    pending = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or (not pending and line.startswith("#")):
            continue
        pending += line
        if pending.endswith("\\"):
            pending = pending[:-1] + " "
            continue
        yield pending
        pending = ""
    if pending:
        yield pending


def expand(value, variables):
    def replacement(match):
        name = match.group(1) or match.group(2)
        if name not in variables:
            raise ValueError(f"unresolved build argument in FROM: {name}")
        return variables[name]

    return VARIABLE.sub(replacement, value)


def normalize_image_ref(value):
    value = value.strip()
    if not value or any(character.isspace() for character in value):
        raise ValueError(f"invalid base image reference: {value!r}")
    name, suffix = value, ""
    if "@" in value:
        name, digest = value.rsplit("@", 1)
        suffix = "@" + digest.lower()
    else:
        slash = value.rfind("/")
        colon = value.rfind(":")
        if colon > slash:
            name, tag = value[:colon], value[colon + 1 :]
            suffix = ":" + tag
        else:
            suffix = ":latest"
    first = name.split("/", 1)[0]
    if "." not in first and ":" not in first and first != "localhost":
        name = "docker.io/" + (name if "/" in name else "library/" + name)
    return name.lower() + suffix


def base_images(dockerfile, build_args):
    variables = {}
    stages = set()
    bases = []
    saw_from = False
    for line in logical_lines(dockerfile.decode("utf-8")):
        instruction, _, body = line.partition(" ")
        instruction = instruction.upper()
        body = body.strip()
        if instruction == "ARG" and not saw_from:
            name, separator, default = body.partition("=")
            name = name.strip()
            if name in build_args:
                variables[name] = build_args[name]
            elif separator:
                variables[name] = expand(default.strip(), variables)
            continue
        if instruction != "FROM":
            continue
        saw_from = True
        parts = body.split()
        while parts and parts[0].startswith("--"):
            parts.pop(0)
        if not parts:
            raise ValueError("FROM has no image reference")
        reference = expand(parts[0], variables)
        if reference.lower() not in stages:
            bases.append(normalize_image_ref(reference))
        if len(parts) >= 3 and parts[1].upper() == "AS":
            stages.add(parts[2].lower())
    if not bases:
        raise ValueError("Dockerfile has no external base image")
    return bases


def build_input_digest(context, dockerfile, build_args):
    context = Path(context).resolve()
    dockerfile = Path(dockerfile).resolve()
    try:
        dockerfile.relative_to(context)
    except ValueError as error:
        raise ValueError("Dockerfile must be inside build context") from error

    dockerfile_bytes = dockerfile.read_bytes()
    digest = hashlib.sha256()
    digest.update(MAGIC)
    digest.update(frame("dockerfile", "Dockerfile", dockerfile_bytes))

    entries = sorted(context.rglob("*"), key=lambda item: item.relative_to(context).as_posix())
    for entry in entries:
        if entry.is_symlink():
            raise ValueError(f"build context contains unsupported symlink: {entry}")
        if entry.is_dir():
            continue
        if not entry.is_file():
            raise ValueError(f"build context contains unsupported entry: {entry}")
        if entry == dockerfile:
            continue
        digest.update(frame("context", entry.relative_to(context).as_posix(), entry.read_bytes()))

    for name, value in sorted(build_args.items()):
        digest.update(frame("build-arg", name, value.encode()))
    for index, reference in enumerate(base_images(dockerfile_bytes, build_args)):
        digest.update(frame("base-image", str(index), reference.encode()))
    return "sha256:" + digest.hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", type=Path, required=True)
    parser.add_argument("--dockerfile", type=Path, required=True)
    parser.add_argument("--build-args", default="")
    args = parser.parse_args()
    value = build_input_digest(
        args.context, args.dockerfile, parse_build_args(args.build_args)
    )
    print(value)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as stream:
            stream.write(f"digest={value}\n")


if __name__ == "__main__":
    main()
