"""Cross-language contract checks for the validation against the JSON Schema contract.

The shared fixtures under `tests/fixtures/schema/` are the single source of
truth of the contract. This runner reads the fixture manifest and checks that
the Python SDK:

- reports no diagnostic for every valid fixture,
- reports exactly the diagnostics the manifest names for every invalid
  fixture, in the order the manifest names them.

The TypeScript runner `tests/contract/schema.test.mts` reads the same
manifest and the same fixtures, so a drift in either SDK fails one of the two
contract targets.

Usage:

    bazel test //tests/contract:schema_py
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from typing import Any

from typcast import Diagnostic
from typcast.numbers import to_binary64
from typcast.schema import validate_schema

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
        directory = candidate / "tests" / "fixtures" / "schema"
        if (directory / MANIFEST_NAME).is_file():
            return directory
    raise SystemExit("schema fixtures not found; run the target through Bazel")


def load_manifest(root: Path) -> dict[str, Any]:
    """Reads the fixture manifest."""
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit("the fixture manifest must be a JSON object")
    return manifest


def listed_files(manifest: dict[str, Any]) -> set[str]:
    """Returns the names of every fixture that the manifest names."""
    names: set[str] = set()
    for section in ("valid", "invalid"):
        for entry in manifest[section]:
            names.add(entry["file"])
    return names


def present_files(root: Path) -> set[str]:
    """Returns the names of every fixture file of the directory."""
    names: set[str] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative == MANIFEST_NAME:
            continue
        names.add(relative)
    return names


def narrow(value: Any) -> Any:
    """Returns the value in the number domain of the document IR.

    The parser of the interpreter keeps an integer of any length, while the
    parser of ECMAScript reads every number in the binary64 domain. The
    validator of the SDK works in the domain of the IR, so the runner narrows
    the numbers of a fixture the same way the TypeScript runner reads them.
    """
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        return to_binary64(value)
    if isinstance(value, float):
        return value
    if isinstance(value, list):
        return [narrow(item) for item in value]
    if isinstance(value, dict):
        return {key: narrow(item) for key, item in value.items()}
    return value


def describe(diagnostic: Diagnostic) -> dict[str, Any]:
    """Returns the comparable fields of a diagnostic."""
    return {
        "code": diagnostic.code,
        "path": diagnostic.path,
        "message": diagnostic.message,
        "details": dict(diagnostic.details),
    }


class SchemaFixtureTests(unittest.TestCase):
    """Checks the shared fixtures against the Python SDK."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = find_fixture_root()
        cls.manifest = load_manifest(cls.root)

    def read(self, name: str) -> Any:
        """Reads one fixture of the shared set."""
        return narrow(
            json.loads((self.root / name).read_text(encoding="utf-8"))
        )

    def test_manifest_lists_every_fixture_file(self) -> None:
        self.assertEqual(
            listed_files(self.manifest),
            present_files(self.root),
            "the manifest and the fixture directory must list the same files",
        )

    def test_valid_fixtures_report_no_diagnostic(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                self.assertEqual(
                    validate_schema(self.read(entry["file"])),
                    (),
                    "a valid fixture must report no diagnostic",
                )

    def test_invalid_fixtures_report_the_expected_diagnostics(self) -> None:
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                actual = validate_schema(self.read(entry["file"]))
                self.assertEqual(
                    [describe(diagnostic) for diagnostic in actual],
                    entry["diagnostics"],
                    "the diagnostics must match the manifest",
                )

    def test_the_diagnostics_are_errors_of_the_validation_phase(self) -> None:
        for section in ("valid", "invalid"):
            for entry in self.manifest[section]:
                with self.subTest(fixture=entry["file"]):
                    for diagnostic in validate_schema(self.read(entry["file"])):
                        self.assertEqual(diagnostic.severity, "error")
                        self.assertEqual(diagnostic.phase, "validation")
                        self.assertIsNone(diagnostic.location)
                        self.assertIsNone(diagnostic.cause)

    def test_the_validator_reports_every_problem_of_a_document(self) -> None:
        # The fixture holds an empty title, an empty text, and an unknown
        # field of the root, so the validator reports three diagnostics in the
        # order of the document.
        entry = next(
            item
            for item in self.manifest["invalid"]
            if item["file"] == "invalid/multiple-problems.json"
        )
        diagnostics = validate_schema(self.read(entry["file"]))
        self.assertEqual(len(diagnostics), len(entry["diagnostics"]))
        self.assertEqual(
            [diagnostic.path for diagnostic in diagnostics],
            [item["path"] for item in entry["diagnostics"]],
            "the diagnostics must come in the order of the document",
        )

    def test_the_validator_never_raises_for_a_broken_instance(self) -> None:
        for section in ("valid", "invalid"):
            for entry in self.manifest[section]:
                with self.subTest(fixture=entry["file"]):
                    # The call must return, whether the instance is valid or
                    # not, and it must not raise an error.
                    validate_schema(self.read(entry["file"]))

    def test_a_value_that_is_not_an_object_is_reported(self) -> None:
        diagnostics = validate_schema("Title")

        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].code, "TYPCAST-SCH-0001")
        self.assertIsNone(diagnostics[0].path)
        self.assertEqual(diagnostics[0].details["keyword"], "type")


if __name__ == "__main__":
    unittest.main()
