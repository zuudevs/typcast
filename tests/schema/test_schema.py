"""Checks of the JSON Schema contract of the document IR.

The stage checks that the contract that the SDKs carry stays in step with the
model of a document and with the fixtures of the repository:

- every keyword that the contract uses is implemented by the validator, so a
  keyword that the contract gains and the validator does not know fails the
  build instead of passing every instance,
- every valid document fixture matches the contract,
- every canonical document of the builder matches the contract.

The TypeScript SDK applies the same rules in
`packages/typescript/tests/schema.test.ts`, and the cross-language runners of
`tests/contract/` compare the diagnostics of both SDKs over the shared schema
fixtures.

Usage:

    bazel test //tests/schema:schema_py
"""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from typing import Any

from typcast.numbers import to_binary64
from typcast.schema import (
    ANNOTATION_KEYWORDS,
    ASSERTION_KEYWORDS,
    SCHEMAS,
    SCHEMA_ROOT,
    schema_keywords,
    validate_schema,
)


def find_directory(*parts: str) -> Path:
    """Locates a directory of the repository in a runfiles tree or a checkout."""
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
        directory = candidate.joinpath(*parts)
        if directory.is_dir():
            return directory
    raise SystemExit(f"the directory {'/'.join(parts)} was not found")


def narrow(value: Any) -> Any:
    """Returns the value in the number domain of the document IR."""
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


class KeywordTests(unittest.TestCase):
    """Checks the keywords that the contract uses."""

    def test_every_keyword_of_the_contract_is_implemented(self) -> None:
        for keyword in schema_keywords():
            with self.subTest(keyword=keyword):
                self.assertTrue(
                    keyword in ANNOTATION_KEYWORDS or keyword in ASSERTION_KEYWORDS,
                    f"the keyword '{keyword}' is not implemented by the validator",
                )

    def test_the_contract_holds_the_schema_of_the_document(self) -> None:
        self.assertIn(SCHEMA_ROOT, SCHEMAS)
        self.assertEqual(
            sorted(SCHEMAS),
            [
                "api/types/alignment.schema.json",
                "api/types/length.schema.json",
                "api/types/paper.schema.json",
                "definitions/bound.schema.json",
                "definitions/node.schema.json",
                "validator.schema.json",
            ],
        )


class FixtureTests(unittest.TestCase):
    """Checks the fixtures of the repository against the contract."""

    def test_every_valid_document_fixture_matches_the_contract(self) -> None:
        root = find_directory("tests", "fixtures", "documents")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        for entry in manifest["valid"]:
            with self.subTest(fixture=entry["file"]):
                value = narrow(
                    json.loads((root / entry["file"]).read_text(encoding="utf-8"))
                )
                diagnostics = validate_schema(value)
                self.assertEqual(
                    [diagnostic.message for diagnostic in diagnostics],
                    [],
                    "a valid fixture must match the schema contract",
                )

    def test_every_canonical_document_of_the_builder_matches_the_contract(self) -> None:
        root = find_directory("tests", "fixtures", "builder")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        for scenario in manifest["scenarios"]:
            if "file" not in scenario:
                continue
            with self.subTest(scenario=scenario["name"]):
                value = narrow(
                    json.loads((root / scenario["file"]).read_text(encoding="utf-8"))
                )
                diagnostics = validate_schema(value)
                self.assertEqual(
                    [diagnostic.message for diagnostic in diagnostics],
                    [],
                    "a canonical document must match the schema contract",
                )


if __name__ == "__main__":
    unittest.main()
