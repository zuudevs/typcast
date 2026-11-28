"""The command line of the schema generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from typcast_schemagen.bundle import read_bundle
from typcast_schemagen.errors import SchemagenError
from typcast_schemagen.renderers import render_python, render_typescript

__all__ = ["build_parser", "main"]

_RENDERERS = {
    "typescript": render_typescript,
    "python": render_python,
}


def build_parser() -> argparse.ArgumentParser:
    """Returns the parser of the command line."""
    parser = argparse.ArgumentParser(
        prog="typcast-schemagen",
        description=(
            "Write the JSON Schema contract of the document IR into a source "
            "file of an SDK."
        ),
    )
    parser.add_argument(
        "--file",
        action="append",
        default=[],
        metavar="PATH=FILE",
        required=True,
        help=(
            "A file of the schema bundle. The path before the sign is the "
            "path of the file relative to the bundle."
        ),
    )
    parser.add_argument(
        "--language",
        choices=sorted(_RENDERERS),
        required=True,
        help="The language of the generated source file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="The file to write.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Runs the generator and returns the exit code of the process."""
    args = build_parser().parse_args(argv)

    try:
        files = _parse_files(args.file)
        documents = read_bundle(files)
        source = _RENDERERS[args.language](documents)
        _write(args.output, source)
    except SchemagenError as error:
        print(f"typcast-schemagen: error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"typcast-schemagen: error: {error}", file=sys.stderr)
        return 2

    return 0


def _parse_files(entries: Sequence[str]) -> dict[str, Path]:
    """Returns the files of the bundle that the arguments name."""
    files: dict[str, Path] = {}
    for entry in entries:
        path, separator, source = entry.partition("=")
        if not separator or not path or not source:
            raise SchemagenError(
                f"'{entry}' is not a path and a file separated by a sign"
            )
        if path in files:
            raise SchemagenError(f"the bundle names '{path}' twice")
        files[path] = Path(source)
    return files


def _write(output: Path, source: str) -> None:
    """Writes the generated source file."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(source, encoding="utf-8", newline="\n")
