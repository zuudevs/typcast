"""Cross-language contract checks for the document IR.

The shared fixtures under `tests/fixtures/documents/` are the single source of
truth of the contract. This runner reads the fixture manifest and checks that
the Python SDK:

- accepts every valid fixture and writes it back in the canonical form,
- rejects every invalid fixture with the diagnostic the manifest names,
- rejects every unserializable fixture when it writes it,
- rejects every invalid object fixture with the diagnostic the manifest names,
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


def listed_files(manifest: dict[str, Any]) -> set[str]:
    """Returns the names of every fixture that the manifest names."""
    names: set[str] = set()
    for section in ("valid", "invalid", "unserializable", "invalid_object"):
        for entry in manifest[section]:
            names.add(entry["file"])
    return names


def at_path(value: Any, path: str) -> Any:
    """Returns the value that a JSON Pointer names."""
    current = value
    for token in path.split("/"):
        if token == "":
            continue
        current = current[token]
    return current


class DocumentFixtureTests(unittest.TestCase):
    """Checks the shared fixtures against the Python SDK."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = find_fixture_root()
        cls.manifest = load_manifest(cls.root)

    def assert_diagnostic(self, error: TypcastError, entry: dict[str, Any]) -> None:
        """Checks a diagnostic against the expectation of the manifest."""
        self.assertTrue(error.diagnostics, "the error must carry a diagnostic")
        diagnostic = error.diagnostics[0]
        self.assertEqual(diagnostic.code, entry["code"])
        self.assertEqual(diagnostic.path, entry["path"])
        self.assertEqual(diagnostic.message, entry["message"])
        details = dict(diagnostic.details)
        # The reason of the parser of the runtime belongs to no expectation of
        # the contract, because the two parsers word their reason
        # differently.
        details.pop("reason", None)
        self.assertEqual(details, entry["details"])

    def test_manifest_lists_every_fixture_file(self) -> None:
        present = {
            path.name for path in self.root.iterdir() if path.is_file()
        }
        present.discard(MANIFEST_NAME)
        self.assertEqual(
            listed_files(self.manifest),
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

    def test_invalid_fixtures_are_rejected_with_the_expected_path(self) -> None:
        # The manifest names the path of every negative fixture, so that the
        # two SDKs point at the same field.
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                with self.assertRaises(TypcastError) as caught:
                    Document.from_json(source)
                self.assertEqual(caught.exception.diagnostics[0].path, entry["path"])

    def test_invalid_fixtures_are_rejected_with_the_expected_message(self) -> None:
        # The manifest names the message of every negative fixture, so that
        # the two SDKs report an invalid input in the same words.
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                with self.assertRaises(TypcastError) as caught:
                    Document.from_json(source)
                self.assertEqual(
                    caught.exception.diagnostics[0].message,
                    entry["message"],
                )

    def test_invalid_fixtures_are_rejected_with_the_expected_details(self) -> None:
        # The manifest names the details of every negative fixture, so that
        # the two SDKs describe an invalid input in the same way.
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                with self.assertRaises(TypcastError) as caught:
                    Document.from_json(source)
                details = dict(caught.exception.diagnostics[0].details)
                # The reason of the parser of the runtime belongs to no
                # expectation of the contract, because the two parsers word
                # their reason differently.
                details.pop("reason", None)
                self.assertEqual(details, entry["details"])

    def test_invalid_fixtures_are_rejected_when_parsed_as_a_value(self) -> None:
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                try:
                    value = json.loads(source)
                except ValueError:
                    # The text is no JSON that the parser of the interpreter
                    # can read, such as an integer token of more than the
                    # limit of the interpreter.
                    continue
                with self.assertRaises(TypcastError) as caught:
                    Document.from_dict(value)
                self.assertEqual(caught.exception.diagnostics[0].code, entry["code"])

    def test_unserializable_fixtures_are_rejected_by_the_writer(self) -> None:
        # The reader accepts these fixtures, because their text is valid
        # JSON, and the writer rejects them, because the canonical text of
        # the IR is UTF-8.
        for entry in self.manifest["unserializable"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                document = Document.from_json(source)
                with self.assertRaises(TypcastError) as caught:
                    document.to_json()
                self.assertEqual(caught.exception.diagnostics[0].code, entry["code"])

    def test_unserializable_fixtures_are_rejected_with_the_expected_diagnostic(
        self,
    ) -> None:
        for entry in self.manifest["unserializable"]:
            with self.subTest(fixture=entry["file"]):
                source = (self.root / entry["file"]).read_text(encoding="utf-8")
                document = Document.from_json(source)
                with self.assertRaises(TypcastError) as caught:
                    document.to_json()
                self.assert_diagnostic(caught.exception, entry)

    def test_invalid_object_fixtures_are_rejected_with_the_expected_diagnostic(
        self,
    ) -> None:
        # The grammar of JSON holds no key that is not a string, so these
        # fixtures name the value that the reader must receive.
        for entry in self.manifest["invalid_object"]:
            with self.subTest(fixture=entry["file"]):
                fixture = json.loads(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                target = at_path(fixture["document"], entry["at"])
                target[1] = target["title"]
                with self.assertRaises(TypcastError) as caught:
                    Document.from_dict(fixture["document"])
                self.assert_diagnostic(caught.exception, entry)


if __name__ == "__main__":
    unittest.main()
