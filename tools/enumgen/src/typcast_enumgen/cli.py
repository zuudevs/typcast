"""The command line of the enum generator."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from typcast_enumgen.catalog import read_catalog_column
from typcast_enumgen.errors import EnumgenError
from typcast_enumgen.renderers import render_python, render_typescript

__all__ = ["build_parser", "main"]

_RENDERERS = {
    "typescript": render_typescript,
    "python": render_python,
}


def build_parser() -> argparse.ArgumentParser:
    """Returns the parser of the command line."""
    parser = argparse.ArgumentParser(
        prog="typcast-enumgen",
        description="Generate a source file of an SDK from a CSV catalog.",
    )
    parser.add_argument(
        "--catalog",
        "-c",
        type=Path,
        required=True,
        help="CSV catalog that holds the values of the enum.",
    )
    parser.add_argument(
        "--column",
        required=True,
        help="Column of the catalog that holds the values of the enum.",
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Name of the generated constant, in upper case.",
    )
    parser.add_argument(
        "--language",
        choices=sorted(_RENDERERS),
        required=True,
        help="Language of the generated source file.",
    )
    parser.add_argument(
        "--label",
        default=None,
        help=(
            "Path of the catalog as it appears in the repository. It names the "
            "catalog in the header of the generated file."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Path of the generated source file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Runs the generator and returns the exit code of the process."""
    args = build_parser().parse_args(argv)

    try:
        values = read_catalog_column(args.catalog, args.column)
        label = args.label if args.label is not None else args.catalog.as_posix()
        text = _RENDERERS[args.language](values, args.name, label)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8", newline="\n")
    except EnumgenError as error:
        print(f"typcast-enumgen: error: {error}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"typcast-enumgen: error: {error}", file=sys.stderr)
        return 1

    return 0
