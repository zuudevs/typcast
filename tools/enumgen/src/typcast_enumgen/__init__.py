"""The expansion of a CSV catalog into a source file of an SDK.

The catalogs of `specs/catalogs/enums/` are the source of truth of every
public enum of the document IR. A catalog that an SDK must enforce at
runtime is expanded into a source file of that SDK, so the SDK holds the
values of the catalog without a hand-written copy that could drift.
"""

from typcast_enumgen.catalog import read_catalog_column
from typcast_enumgen.errors import EnumgenError
from typcast_enumgen.renderers import render_python, render_typescript

__all__ = [
    "EnumgenError",
    "read_catalog_column",
    "render_python",
    "render_typescript",
]
