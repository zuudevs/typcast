import argparse
import sys
from pathlib import Path
from typing import Sequence

from typcast_codegen.errors import CodegenError
from typcast_codegen.pipeline import generate_json_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="typcast-codegen",
        description="Generate JSON files from Typcast templates.",
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Input JSON template.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Generated JSON output path.",
    )
    parser.add_argument(
        "--catalog",
        action="append",
        type=Path,
        default=[],
        help=(
            "Catalog that the build declares as an input of the template. "
            "Repeat the option for every catalog. Every placeholder of the "
            "template must resolve to one of them."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        generate_json_file(args.input, args.output, args.catalog)
    except CodegenError as error:
        print(f"typcast-codegen: error: {error}", file=sys.stderr)
        return 1

    return 0
