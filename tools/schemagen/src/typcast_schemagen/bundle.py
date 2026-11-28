"""The reading of a schema bundle for the schema generator.

The bundle is the artifact set that `//specs/schemas:schema_bundle`
produces, and it is the set that the release publishes. The generator reads
every file of the bundle and keeps the path of the file relative to the
bundle, because the `$ref` values of the bundle are relative to the document
that holds them.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from typcast_schemagen.errors import SchemagenError

__all__ = ["read_bundle"]


def read_bundle(files: Mapping[str, Path]) -> dict[str, Any]:
    """Returns the schema documents of the bundle.

    The argument maps the path of every file relative to the bundle to the
    file itself. The returned mapping uses the same paths as its keys.
    """
    if not files:
        raise SchemagenError("the bundle holds no schema document")
    documents: dict[str, Any] = {}
    for path in sorted(files):
        documents[path] = _read_document(files[path])
    return documents


def _read_document(path: Path) -> Any:
    """Reads one schema document of the bundle."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise SchemagenError(f"cannot read '{path}': {error}") from None
    try:
        document = json.loads(text)
    except ValueError as error:
        raise SchemagenError(f"'{path}' is not valid JSON: {error}") from None
    if not isinstance(document, dict):
        raise SchemagenError(f"'{path}' is not a JSON object")
    return document
