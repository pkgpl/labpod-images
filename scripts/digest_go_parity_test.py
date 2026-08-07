"""Differential vectors against LabPod's Go `format.DefinitionDigest`.

The server recomputes this digest from a template's live definition and pulls
the published image only when the two agree, so a divergence here never
surfaces as an error -- it silently degrades every install to a local build.
`digest_vectors.json` is generated from that Go implementation and pins the
normalization rules the two could plausibly drift on.
"""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build-input-digest.py")
SPEC = importlib.util.spec_from_file_location("build_input_digest", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

ROOT = Path(__file__).resolve().parent.parent
VECTORS = json.loads((Path(__file__).with_name("digest_vectors.json")).read_text())


class GoParityTest(unittest.TestCase):
    def test_every_vector_matches_the_go_implementation(self):
        self.assertGreaterEqual(len(VECTORS), 10)
        for vector in VECTORS:
            with self.subTest(vector=vector["name"]), tempfile.TemporaryDirectory() as directory:
                context = Path(directory)
                (context / "Dockerfile").write_text(vector["dockerfile"])
                for relative, contents in vector["context"].items():
                    target = context / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(contents)
                digest = MODULE.build_input_digest(
                    context, context / "Dockerfile", vector["build_args"]
                )
                self.assertEqual(digest, vector["digest"])

    def test_published_catalog_digests_still_reproduce(self):
        catalog = json.loads((ROOT / "published-images.json").read_text())
        for image in catalog["images"]:
            context = ROOT / Path(image["dockerfile"]).parent
            artifacts = [(image["published"], image["build_args"])]
            for variant in image["published"].get("variants", []):
                artifacts.append((variant, variant.get("build_args", {})))
            for artifact, build_args in artifacts:
                with self.subTest(ref=artifact["ref"]):
                    digest = MODULE.build_input_digest(
                        context, ROOT / image["dockerfile"], build_args
                    )
                    self.assertEqual(digest, artifact["definition_digest"])


if __name__ == "__main__":
    unittest.main()
