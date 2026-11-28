"""The schema generator of Typcast.

The generator writes the JSON Schema contract of the document IR into a
source file of an SDK, so that the SDK carries the contract and needs no file
of the repository at run time.
"""

from typcast_schemagen.bundle import read_bundle
from typcast_schemagen.errors import SchemagenError
from typcast_schemagen.renderers import render_python, render_typescript

__all__ = [
    "SchemagenError",
    "read_bundle",
    "render_python",
    "render_typescript",
]
