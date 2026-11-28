"""Cross-language contract checks for the Typst emitter.

The shared fixtures under `tests/fixtures/` are the single source of truth of
the contract. This runner reads the document manifest and checks that the
Python SDK:

- emits the source that the golden file holds for every valid document, byte
  for byte,
- emits the same source when it emits the same document twice,
- writes the output with the encoding and the line endings of the output
  contract.

The TypeScript runner `tests/contract/typst.test.mts` reads the same manifest
and the same golden files, so a drift in either SDK fails one of the two
contract targets.

Usage:

    bazel test //tests/contract:typst_py
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from typing import Any

from typcast import Document

MANIFEST_NAME = "manifest.json"
DOCUMENTS_DIRECTORY = "documents"
EXPECTED_DIRECTORY = "expected"


def find_fixture_root() -> Path:
    """Locates the shared fixtures in a Bazel runfiles tree or in a checkout."""
    candidates: list[Path] = []
    runfiles = os.environ.get("RUNFILES_DIR")
    workspace = os.environ.get("TEST_WORKSPACE")
    if runfiles:
        base = Path(runfiles)
        candidates.append(base)
        if workspace:
            candidates.append(base / workspace)
        candidates.append(base / "_main")
    cwd = Path.cwd()
    candidates.append(cwd)
    if workspace:
        candidates.append(cwd / workspace)
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    for candidate in candidates:
        directory = candidate / "tests" / "fixtures"
        if (directory / DOCUMENTS_DIRECTORY / MANIFEST_NAME).is_file():
            return directory
    raise SystemExit("document fixtures not found; run the target through Bazel")


def load_manifest(root: Path) -> dict[str, Any]:
    """Reads the document manifest."""
    manifest = json.loads(
        (root / DOCUMENTS_DIRECTORY / MANIFEST_NAME).read_text(encoding="utf-8")
    )
    if not isinstance(manifest, dict):
        raise SystemExit("the document manifest must be a JSON object")
    return manifest


def expected_name(document_name: str) -> str:
    """Returns the name of the golden file of a document fixture."""
    return f"{Path(document_name).stem}.typ"


class TypstFixtureTests(unittest.TestCase):
    """Checks the golden files against the Python SDK."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = find_fixture_root()
        cls.manifest = load_manifest(cls.root)

    def read_document(self, name: str) -> Document:
        """Reads one document fixture of the shared set."""
        value = json.loads(
            (self.root / DOCUMENTS_DIRECTORY / name).read_text(encoding="utf-8")
        )
        return Document.from_dict(value)

    def test_every_valid_document_has_a_golden_file(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                golden = self.root / EXPECTED_DIRECTORY / expected_name(entry["file"])
                self.assertTrue(
                    golden.is_file(),
                    f"the golden file '{golden.name}' must exist",
                )

    def test_the_emitter_writes_the_golden_file(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                golden = (
                    self.root / EXPECTED_DIRECTORY / expected_name(entry["file"])
                ).read_bytes()
                actual = self.read_document(entry["file"]).to_typst().encode("utf-8")
                self.assertEqual(
                    actual,
                    golden,
                    "the emitted source must match the golden file byte for byte",
                )

    def test_the_emitter_is_deterministic(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                document = self.read_document(entry["file"])
                self.assertEqual(
                    document.to_typst(),
                    document.to_typst(),
                    "the same document must produce the same source",
                )

    def test_the_output_holds_the_encoding_and_the_endings_of_the_contract(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                source = self.read_document(entry["file"]).to_typst()
                encoded = source.encode("utf-8")
                self.assertFalse(encoded.startswith(b"\xef\xbb\xbf"), "no byte order mark")
                self.assertNotIn(b"\r", encoded, "the line endings must be LF")
                self.assertTrue(source.endswith("\n"), "the output ends with a newline")
                self.assertFalse(
                    source.endswith("\n\n"),
                    "the output ends with exactly one newline",
                )

    def test_the_output_starts_with_the_header(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                source = self.read_document(entry["file"]).to_typst()
                self.assertTrue(
                    source.startswith("// Generated by Typcast. Do not edit.\n"),
                    "the output starts with the header of the contract",
                )


if __name__ == "__main__":
    unittest.main()
