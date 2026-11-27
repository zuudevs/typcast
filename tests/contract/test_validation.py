"""Cross-language contract checks for the validation engine.

The shared fixtures under `tests/fixtures/validation/` are the single source of
truth of the contract. This runner reads the fixture manifest and checks that
the Python SDK:

- reports no diagnostic for every valid fixture,
- reports exactly the diagnostics the manifest names for every invalid
  fixture, in the order the manifest names them.

The TypeScript runner `tests/contract/validation.test.mts` reads the same
manifest and the same fixtures, so a drift in either SDK fails one of the two
contract targets.

Usage:

    bazel test //tests/contract:validation_py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any

from typcast import Diagnostic, Document, TypcastConfig

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
        directory = candidate / "tests" / "fixtures" / "validation"
        if (directory / MANIFEST_NAME).is_file():
            return directory
    raise SystemExit("validation fixtures not found; run the target through Bazel")


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


def config_of(entry: dict[str, Any]) -> TypcastConfig | None:
    """Returns the configuration of a fixture, when the fixture names one."""
    limit = entry.get("maxRawBytes")
    if limit is None:
        return None
    return TypcastConfig(max_raw_bytes=limit)


def describe(diagnostic: Diagnostic) -> dict[str, Any]:
    """Returns the comparable fields of a diagnostic."""
    return {
        "code": diagnostic.code,
        "path": diagnostic.path,
        "message": diagnostic.message,
        "details": dict(diagnostic.details),
    }


class ValidationFixtureTests(unittest.TestCase):
    """Checks the shared fixtures against the Python SDK."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = find_fixture_root()
        cls.manifest = load_manifest(cls.root)

    def test_manifest_lists_every_fixture_file(self) -> None:
        self.assertEqual(
            listed_files(self.manifest),
            present_files(self.root),
            "the manifest and the fixture directory must list the same files",
        )

    def test_valid_fixtures_report_no_diagnostic(self) -> None:
        for entry in self.manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                document = Document.from_json(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    document.validate(config_of(entry)),
                    (),
                    "a valid fixture must report no diagnostic",
                )

    def test_invalid_fixtures_report_the_expected_diagnostics(self) -> None:
        for entry in self.manifest["invalid"]:
            with self.subTest(fixture=entry["file"]):
                document = Document.from_json(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                expected = entry["diagnostics"]
                actual = document.validate(config_of(entry))
                self.assertEqual(
                    [describe(diagnostic) for diagnostic in actual],
                    expected,
                    "the diagnostics must match the manifest",
                )

    def test_the_diagnostics_are_errors_of_the_validation_phase(self) -> None:
        for section in ("valid", "invalid"):
            for entry in self.manifest[section]:
                with self.subTest(fixture=entry["file"]):
                    document = Document.from_json(
                        (self.root / entry["file"]).read_text(encoding="utf-8")
                    )
                    for diagnostic in document.validate(config_of(entry)):
                        self.assertEqual(diagnostic.severity, "error")
                        self.assertEqual(diagnostic.phase, "validation")
                        self.assertIsNone(diagnostic.location)
                        self.assertIsNone(diagnostic.cause)

    def test_the_engine_reports_every_problem_of_a_document(self) -> None:
        # The fixture holds a table with two broken rows, an oversized raw
        # span, and a duplicated module alias, so the engine reports four
        # diagnostics in the order of the document.
        entry = next(
            item
            for item in self.manifest["invalid"]
            if item["file"] == "invalid/multiple-problems.json"
        )
        document = Document.from_json(
            (self.root / entry["file"]).read_text(encoding="utf-8")
        )
        diagnostics = document.validate(config_of(entry))
        self.assertEqual(len(diagnostics), len(entry["diagnostics"]))
        self.assertEqual(
            [diagnostic.path for diagnostic in diagnostics],
            [item["path"] for item in entry["diagnostics"]],
            "the diagnostics must come in the order of the document",
        )

    def test_the_engine_never_raises_for_a_semantic_problem(self) -> None:
        for section in ("valid", "invalid"):
            for entry in self.manifest[section]:
                with self.subTest(fixture=entry["file"]):
                    document = Document.from_json(
                        (self.root / entry["file"]).read_text(encoding="utf-8")
                    )
                    # The call must return, whether the document is valid or
                    # not, and it must not raise an error.
                    document.validate(config_of(entry))


if __name__ == "__main__":
    unittest.main()
