"""Cross-language contract checks for the document IR.

The shared fixtures under `tests/fixtures/documents/` are the single source of
truth of the contract. This runner reads the fixture manifest and checks that
the Python SDK:

- accepts every valid fixture and writes it back in the canonical form,
- rejects every invalid fixture with the diagnostic code the manifest names,
- keeps the fixture set and the manifest in agreement.

The TypeScript runner `tests/contract/contract.test.mts` reads the same
manifest and the same fixtures, so a drift in either SDK fails one of the two
contract targets.

Usage:

    bazel test //tests/contract:contract_py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any

from typcast import (
    SCHEMA_VERSION,
    Document,
    SerializationError,
    TypcastError,
    ValidationError,
)

MANIFEST_NAME = "manifest.json"


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
        directory = candidate / "tests" / "fixtures" / "documents"
        if (directory / MANIFEST_NAME).is_file():
            return directory
    raise SystemExit("document fixtures not found; run the target through Bazel")


def load_manifest(root: Path) -> dict[str, Any]:
    """Reads the fixture manifest."""
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit("the fixture manifest must be a JSON object")
    return manifest


class DocumentFixtureTests(unittest.TestCase):
    """Checks the shared fixtures against the Python SDK."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = find_fixture_root()
        cls.manifest = load_manifest(cls.root)

    def test_manifest_lists_every_fixture_file(self) -> None:
        listed = {entry["file"] for entry in self.manifest["valid"]}
        listed |= {entry["file"] for entry in self.manifest["invalid"]}
        present = {
            path.name for path in self.root.iterdir() if path.is_file()
        }
        present.discard(MANIFEST_NAME)
        self.assertEqual(
            listed,
            present,
            "the manifest and the fixture directory must list the same files",
        )

    def test_the_sdk_and_the_fixtures_use_the_same_contract_version(self) -> None:
        contract = ".".join(SCHEMA_VERSION.split(".")[:2])
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                value = json.loads(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                version = value["schemaVersion"]
                self.assertEqual(
                    ".".join(version.split(".")[:2]),
                    contract,
                    "the SDK and the fixtures must use the same contract version",
                )

    def test_valid_fixtures_round_trip_in_the_canonical_form(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_bytes()
                document = Document.from_json(source.decode("utf-8"))
                self.assertEqual(
                    document.to_json().encode("utf-8"),
                    source,
                    "the canonical form must reproduce the fixture byte for byte",
                )
                again = Document.from_json(document.to_json())
                self.assertEqual(again.to_dict(), document.to_dict())

    def test_valid_fixtures_expose_their_model(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                document = Document.from_json(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                self.assertIsInstance(document, Document)
                self.assertTrue(document.contents)
                self.assertIsInstance(document.schema_version, str)

    def test_invalid_fixtures_are_rejected_with_the_expected_code(self) -> None:
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                with self.assertRaises(TypcastError) as caught:
                    Document.from_json(source)
                error = caught.exception
                self.assertTrue(
                    isinstance(error, (ValidationError, SerializationError)),
                    f"unexpected error type: {type(error).__name__}",
                )
                self.assertTrue(error.diagnostics, "the error must carry a diagnostic")
                self.assertEqual(error.diagnostics[0].code, entry["code"])

    def test_invalid_fixtures_are_rejected_when_parsed_as_a_value(self) -> None:
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                try:
                    value = json.loads(source)
                except json.JSONDecodeError:
                    continue
                with self.assertRaises(TypcastError) as caught:
                    Document.from_dict(value)
                self.assertEqual(caught.exception.diagnostics[0].code, entry["code"])


if __name__ == "__main__":
    unittest.main()
