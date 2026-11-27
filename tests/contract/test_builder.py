"""Cross-language contract checks for the fluent builder.

The shared fixtures under `tests/fixtures/builder/` are the single source of
truth of the contract. The manifest names the scenarios and the operations of
the builder, and every scenario names the canonical JSON that the builder
must produce. This runner reads the manifest, builds every scenario with the
Python SDK, and checks that the canonical JSON of the document matches the
fixture byte for byte.

The TypeScript runner `tests/contract/builder.test.mts` reads the same
manifest and the same fixtures, so a drift in either SDK fails one of the two
contract targets.

Usage:

    bazel test //tests/contract:builder_py
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from typing import Any

from typcast import (
    Document,
    DocumentBuilder,
    Length,
    bold,
    column,
    italic,
    line_break,
    link,
    monospace,
    raw_inline,
    text,
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
        directory = candidate / "tests" / "fixtures" / "builder"
        if (directory / MANIFEST_NAME).is_file():
            return directory
    raise SystemExit("builder fixtures not found; run the target through Bazel")


def load_manifest(root: Path) -> dict[str, Any]:
    """Reads the fixture manifest."""
    manifest = json.loads((root / MANIFEST_NAME).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise SystemExit("the fixture manifest must be a JSON object")
    return manifest


def listed_files(manifest: dict[str, Any]) -> set[str]:
    """Returns the names of every fixture that the manifest names."""
    return {entry["file"] for entry in manifest["scenarios"]}


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


def span_of(item: Any) -> Any:
    """Returns the content value of one item of a content collection."""
    if isinstance(item, str):
        return item
    kind = item["span"]
    if kind == "text":
        return text(item["value"])
    if kind == "bold":
        return bold(*content_of(item["content"]))
    if kind == "italic":
        return italic(*content_of(item["content"]))
    if kind == "monospace":
        return monospace(*content_of(item["content"]))
    if kind == "link":
        return link(item["href"], *content_of(item["content"]))
    if kind == "line_break":
        return line_break()
    if kind == "raw_inline":
        return raw_inline(item["value"], item["format"])
    raise SystemExit(f"unknown span helper: {kind}")


def content_of(items: list[Any]) -> tuple[Any, ...]:
    """Returns the content values of a content collection."""
    return tuple(span_of(item) for item in items)


def build_scenario(operations: list[dict[str, Any]]) -> Document:
    """Builds the document of a scenario with the Python builder."""
    builder = DocumentBuilder()
    for operation in operations:
        kind = operation["op"]
        if kind == "title":
            builder.title(operation["value"])
        elif kind == "author":
            builder.author(operation["value"])
        elif kind == "date":
            builder.date(operation["value"])
        elif kind == "page":
            margin = operation.get("margin")
            builder.page(
                paper=operation.get("paper", "a4"),
                orientation=operation.get("orientation", "portrait"),
                margin=(
                    None
                    if margin is None
                    else Length(margin["value"], margin["unit"])
                ),
            )
        elif kind == "heading":
            builder.heading(
                operation["level"],
                *content_of(operation["content"]),
            )
        elif kind == "paragraph":
            builder.paragraph(*content_of(operation["content"]))
        elif kind == "bullet_list":
            builder.bullet_list(
                [content_of(item) for item in operation["items"]]
            )
        elif kind == "numbered_list":
            builder.numbered_list(
                [content_of(item) for item in operation["items"]]
            )
        elif kind == "table":
            builder.table(
                columns=[
                    column(
                        content_of(entry["header"]),
                        align=entry.get("align", "left"),
                    )
                    for entry in operation["columns"]
                ],
                rows=[
                    [content_of(cell) for cell in row]
                    for row in operation["rows"]
                ],
            )
        elif kind == "image":
            caption = operation.get("caption")
            builder.image(
                operation["path"],
                alt=operation["alt"],
                caption=None if caption is None else content_of(caption),
            )
        elif kind == "page_break":
            builder.page_break()
        elif kind == "raw":
            builder.raw(
                operation["value"],
                format=operation.get("format", "markup"),
            )
        elif kind == "module":
            builder.module(
                operation["path"],
                alias=operation.get("alias"),
                items=operation.get("items"),
            )
        else:
            raise SystemExit(f"unknown builder operation: {kind}")
    return builder.build()


class BuilderFixtureTests(unittest.TestCase):
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

    def test_every_scenario_matches_its_canonical_json(self) -> None:
        for entry in self.manifest["scenarios"]:
            with self.subTest(scenario=entry["name"]):
                document = build_scenario(entry["operations"])
                source = (self.root / entry["file"]).read_bytes()
                self.assertEqual(
                    document.to_json().encode("utf-8"),
                    source,
                    "the builder must produce the canonical JSON of the fixture",
                )

    def test_every_scenario_round_trips_through_the_reader(self) -> None:
        for entry in self.manifest["scenarios"]:
            with self.subTest(scenario=entry["name"]):
                document = build_scenario(entry["operations"])
                again = Document.from_json(document.to_json())
                self.assertEqual(again.to_dict(), document.to_dict())

    def test_every_scenario_is_readable_as_a_json_value(self) -> None:
        for entry in self.manifest["scenarios"]:
            with self.subTest(scenario=entry["name"]):
                value = json.loads(
                    (self.root / entry["file"]).read_text(encoding="utf-8")
                )
                document = Document.from_dict(value)
                self.assertEqual(document.to_dict(), value)


if __name__ == "__main__":
    unittest.main()
