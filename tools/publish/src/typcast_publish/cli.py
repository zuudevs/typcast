"""Command line interface for the schema publisher."""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from typcast_publish.archive import (
    ARCHIVE_PREFIX,
    bundle_sources,
    write_archive,
)
from typcast_publish.errors import PublishError
from typcast_publish.publisher import (
    DEFAULT_TIMEOUT,
    PUBLISHED_BASE,
    check_published_bundle,
    publish_bundle,
    published_url,
    read_manifest,
    verify_published_urls,
    write_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="typcast-publish",
        description="Publish the Typcast schema bundle under a release tag.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    manifest = commands.add_parser(
        "manifest",
        help="Write the list of the files in the bundle.",
    )
    manifest.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="File that receives the manifest.",
    )
    manifest.add_argument(
        "paths",
        nargs="+",
        help="Relative path of every bundle file.",
    )

    publish = commands.add_parser(
        "publish",
        help="Write the published bundle for a release tag.",
    )
    publish.add_argument(
        "--version",
        required=True,
        help="Release tag, for example v1.0.0.",
    )
    publish.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Built schema bundle directory.",
    )
    publish.add_argument(
        "--manifest",
        "-m",
        type=Path,
        required=True,
        help="Manifest of the bundle files.",
    )
    publish.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="Directory that receives the published bundle.",
    )

    check = commands.add_parser(
        "check",
        help="Compare a published bundle with the built bundle.",
    )
    check.add_argument(
        "--version",
        required=True,
        help="Release tag, for example v1.0.0.",
    )
    check.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Built schema bundle directory.",
    )
    check.add_argument(
        "--manifest",
        "-m",
        type=Path,
        required=True,
        help="Manifest of the bundle files.",
    )
    check.add_argument(
        "--published",
        "-p",
        type=Path,
        required=True,
        help="Directory that holds the published bundle.",
    )

    verify = commands.add_parser(
        "verify",
        help="Check that every published schema resolves at its versioned raw URL.",
    )
    verify.add_argument(
        "--version",
        required=True,
        help="Release tag, for example v1.0.0.",
    )
    verify.add_argument(
        "--manifest",
        "-m",
        type=Path,
        required=True,
        help="Manifest of the bundle files.",
    )
    verify.add_argument(
        "--published",
        "-p",
        type=Path,
        required=True,
        help="Directory that holds the published bundle.",
    )
    verify.add_argument(
        "--base-url",
        default=PUBLISHED_BASE,
        help="Base URL of the published files.",
    )
    verify.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="Timeout of one request, in seconds.",
    )

    archive = commands.add_parser(
        "archive",
        help="Write the deterministic archive of the schema bundle.",
    )
    archive.add_argument(
        "--input",
        "-i",
        type=Path,
        default=None,
        help="Directory that holds the schema files.",
    )
    archive.add_argument(
        "--manifest",
        "-m",
        type=Path,
        default=None,
        help="Manifest of the bundle files.",
    )
    archive.add_argument(
        "--file",
        dest="files",
        action="append",
        default=[],
        metavar="NAME=PATH",
        help="One bundle file: its path in the bundle and the path of the file.",
    )
    archive.add_argument(
        "--output",
        "-o",
        type=Path,
        required=True,
        help="File that receives the archive.",
    )
    archive.add_argument(
        "--prefix",
        default=ARCHIVE_PREFIX,
        help="Directory prefix inside the archive.",
    )

    return parser


def _manifest(args: argparse.Namespace) -> int:
    write_manifest(list(args.paths), args.output)
    print(f"wrote {len(args.paths)} paths to {args.output}")
    return 0


def _publish(args: argparse.Namespace) -> int:
    manifest = read_manifest(args.manifest)
    published = publish_bundle(args.input, manifest, args.output, args.version)
    for relative_path in published:
        print(published_url(args.version, relative_path))
    print(f"published {len(published)} schema files")
    return 0


def _check(args: argparse.Namespace) -> int:
    manifest = read_manifest(args.manifest)
    problems = check_published_bundle(
        args.input,
        manifest,
        args.published,
        args.version,
    )
    for problem in problems:
        print(f"typcast-publish: error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print("the published bundle matches the build")
    return 0


def _verify(args: argparse.Namespace) -> int:
    manifest = read_manifest(args.manifest)
    problems = verify_published_urls(
        args.version,
        manifest,
        args.published,
        base_url=args.base_url,
        timeout=args.timeout,
    )
    for problem in problems:
        print(f"typcast-publish: error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"every published schema resolves at its versioned raw URL ({len(manifest)} files)")
    return 0


def _archive(args: argparse.Namespace) -> int:
    if args.files:
        sources = []
        for entry in args.files:
            name, separator, path = entry.partition("=")
            if not separator or not name or not path:
                raise PublishError(
                    f"invalid file entry {entry!r}; expected NAME=PATH"
                )
            sources.append((name, Path(path)))
    else:
        if args.input is None or args.manifest is None:
            raise PublishError(
                "the archive needs --input and --manifest, or one --file per member"
            )
        sources = bundle_sources(args.input, read_manifest(args.manifest))

    names = write_archive(sources, args.output, prefix=args.prefix)
    for name in names:
        print(name)
    print(f"wrote {len(names)} files to {args.output}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if args.command == "manifest":
            return _manifest(args)
        if args.command == "publish":
            return _publish(args)
        if args.command == "verify":
            return _verify(args)
        if args.command == "archive":
            return _archive(args)
        return _check(args)
    except PublishError as error:
        print(f"typcast-publish: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
