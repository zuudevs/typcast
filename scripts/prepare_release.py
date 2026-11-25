"""Prepare the release commit of a Typcast release.

The command sets the release version in every manifest and in every schema
source, publishes the built schema bundle under `specs/schemas/`, and verifies
the result. The maintainer writes the changelog entry, runs this command,
commits the result, and tags the commit.

The published bundle is the file set that the tagged commit carries, so every
versioned raw URL resolves at the tag. The command creates neither a commit
nor a tag; the release procedure in `docs/development/release.md` describes the
steps around it.

The publication needs a bundle that was built after the version bump, because
the build carries the identity of the sources. The procedure therefore runs
the command twice: once to set the versions, and once to publish the bundle
that the build produced.

The command uses the Python standard library only, so it needs no SDK
installation and no network access.

Usage:

    python scripts/prepare_release.py --version v1.0.0 [--root PATH]
        [--bundle DIR] [--manifest FILE] [--published DIR] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from check_version import (
    CHANGELOG,
    MANIFESTS,
    MODULE_FIELD_RE,
    MODULE_VERSION_RE,
    SCHEMA_SOURCES,
    changelog_versions,
    check_versions,
    find_root,
)

# The root of the schema bundle in the repository. The published paths are
# relative to it.
SCHEMA_ROOT = "specs/schemas/"

try:
    from typcast_publish.errors import PublishError
    from typcast_publish.publisher import (
        check_published_bundle,
        compare_archives,
        publish_bundle,
        read_manifest,
        validate_version,
    )
except ModuleNotFoundError:
    # The Bazel target puts the publisher library on the import path. The
    # fallback lets the command run with the system Python as well.
    sys.path.insert(
        0,
        str(Path(__file__).resolve().parents[1] / "tools" / "publish" / "src"),
    )
    from typcast_publish.errors import PublishError
    from typcast_publish.publisher import (
        check_published_bundle,
        compare_archives,
        publish_bundle,
        read_manifest,
        validate_version,
    )

# The identity of a schema source names the version of the contract. The
# publisher replaces the version segment with the release tag, so the source
# and the published file carry the same identity when the versions agree.
SCHEMA_ID_SEGMENT_RE = re.compile(
    r"(https://raw\.githubusercontent\.com/zuudevs/typcast/)"
    r"v?\d+\.\d+\.\d+(/specs/schemas/)"
)

# The project table of a Python manifest. The version lives in that table.
PYPROJECT_PROJECT_RE = re.compile(r"(?ms)^\[project\][^\n]*\n(.*?)(?=^\[|\Z)")
PYPROJECT_VERSION_RE = re.compile(r'(?m)^version\s*=\s*"[^"]+"[^\n]*$')


class PrepareError(Exception):
    """An error that stops the preparation."""


def module_text(text: str, version: str) -> str:
    """Returns the Bazel module file with the given version."""
    match = MODULE_VERSION_RE.search(text)
    if not match:
        raise PrepareError("the Bazel module has no module block")
    block = match.group(1)
    updated, count = MODULE_FIELD_RE.subn(
        'version = "%s"' % version,
        block,
        count=1,
    )
    if count != 1:
        raise PrepareError("the Bazel module has no version field")
    return text[: match.start(1)] + updated + text[match.end(1) :]


def json_text(text: str, version: str) -> str:
    """Returns the JSON manifest with the given version."""
    try:
        document = json.loads(text)
    except json.JSONDecodeError as error:
        raise PrepareError(f"invalid JSON manifest: {error}") from error
    if not isinstance(document, dict):
        raise PrepareError("a JSON manifest must be an object")
    document["version"] = version
    return json.dumps(document, ensure_ascii=False, indent=2) + "\n"


def pyproject_text(text: str, version: str) -> str:
    """Returns the Python manifest with the given version."""
    match = PYPROJECT_PROJECT_RE.search(text)
    if not match:
        raise PrepareError("the Python manifest has no project table")
    section = match.group(1)
    updated, count = PYPROJECT_VERSION_RE.subn(
        'version = "%s"' % version,
        section,
        count=1,
    )
    if count != 1:
        raise PrepareError("the Python manifest has no version in the project table")
    return text[: match.start(1)] + updated + text[match.end(1) :]


def schema_text(text: str, tag: str) -> str:
    """Returns the schema source with the identity of the given release tag."""
    updated, count = SCHEMA_ID_SEGMENT_RE.subn(
        lambda match: "%s%s%s" % (match.group(1), tag, match.group(2)),
        text,
    )
    if count == 0:
        raise PrepareError("the schema source has no identity")
    return updated


def version_updates(root: Path, version: str, tag: str) -> list[tuple[Path, str]]:
    """Returns the new text of every file that carries the release version.

    The list holds only the files whose content changes, so the preparation
    reports the same set on a second run.
    """
    updates: list[tuple[Path, str]] = []

    for relative_path, description in MANIFESTS:
        path = root / relative_path
        if not path.is_file():
            raise PrepareError(f"missing {description}: {relative_path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".toml":
            updated = pyproject_text(text, version)
        elif path.suffix == ".json":
            updated = json_text(text, version)
        else:
            updated = module_text(text, version)
        if updated != text:
            updates.append((path, updated))

    for relative_path, description in SCHEMA_SOURCES:
        path = root / relative_path
        if not path.is_file():
            raise PrepareError(f"missing {description}: {relative_path}")
        text = path.read_text(encoding="utf-8")
        updated = schema_text(text, tag)
        if updated != text:
            updates.append((path, updated))

    return updates


def changelog_problems(root: Path, version: str) -> list[str]:
    """Returns the problems of the changelog of the release.

    The release notes are written by the maintainer. The preparation refuses
    to run without them, because a release without an entry has no notes.
    """
    changelog = root / CHANGELOG
    if not changelog.is_file():
        return [f"missing changelog: {CHANGELOG}"]
    if version not in changelog_versions(changelog):
        return [
            f"the changelog has no entry for {version}: {CHANGELOG}; write the "
            "release notes before the preparation"
        ]
    return []


def generated_files(manifest: list[str]) -> list[str]:
    """Returns the files of the manifest that the build generates.

    The sources of the bundle are tracked files of the repository. Every other
    file of the manifest is a build output. The release commit carries it,
    because the versioned raw URL serves it, and the development branch must
    not carry it, because it would drift from its template.

    Every tracked schema of the bundle belongs to `SCHEMA_SOURCES`, because
    the release version check reads the contract version of every source. A
    new tracked schema therefore needs an entry there, and the cleanup keeps
    the file.
    """
    sources = {
        relative_path[len(SCHEMA_ROOT) :]
        for relative_path, _ in SCHEMA_SOURCES
        if relative_path.startswith(SCHEMA_ROOT)
    }
    return [
        relative_path for relative_path in manifest if relative_path not in sources
    ]


def clean_published(published: Path, manifest: list[str]) -> list[str]:
    """Removes the generated published files and returns their paths."""
    removed: list[str] = []

    for relative_path in generated_files(manifest):
        target = published / relative_path
        if not target.is_file():
            continue
        target.unlink()
        removed.append(relative_path)

    for relative_path in removed:
        directory = (published / relative_path).parent
        while directory != published and directory.is_dir():
            if any(directory.iterdir()):
                break
            directory.rmdir()
            directory = directory.parent

    return removed


def verify_release(
    root: Path,
    tag: str,
    bundle: Path | None = None,
    manifest_path: Path | None = None,
    published: Path | None = None,
) -> list[str]:
    """Returns the problems of the prepared release tree.

    An empty list means that every manifest, every schema source, and the
    changelog agree with the release tag. When the bundle is given, it also
    means that the published bundle is the built bundle with the identity of
    the tag and that the archive of the published bundle is the archive of the
    build.
    """
    problems = list(check_versions(root, tag))
    if bundle is None or manifest_path is None or published is None:
        return problems

    manifest = read_manifest(manifest_path)
    problems.extend(check_published_bundle(bundle, manifest, published, tag))
    problems.extend(compare_archives(bundle, manifest, published))
    return problems


def clean_release(
    published: Path,
    manifest_path: Path,
    dry_run: bool = False,
) -> list[str]:
    """Removes the generated published files and returns their paths.

    The cleanup runs after the release, on the development branch. It removes
    the files that the build generates and keeps the tracked schemas, so that
    the development branch carries the sources and the templates only.
    """
    manifest = read_manifest(manifest_path)
    generated = generated_files(manifest)
    if dry_run:
        return generated
    return clean_published(published, manifest)


def prepare(
    root: Path,
    tag: str,
    bundle: Path | None = None,
    manifest_path: Path | None = None,
    published: Path | None = None,
    dry_run: bool = False,
    clean: bool = False,
) -> int:
    """Prepares the release tree and returns the exit code of the command."""
    validate_version(tag)
    version = tag[1:]

    if published is None:
        published = root / "specs" / "schemas"

    if clean:
        if bundle is not None:
            raise PrepareError("the cleanup does not publish a bundle")
        return clean_published_bundle(
            tag, published, manifest_path, dry_run
        )

    problems = changelog_problems(root, version)
    if problems:
        raise PrepareError(problems[0])

    if bundle is not None and manifest_path is None:
        raise PrepareError("the publication needs --bundle and --manifest together")
    if manifest_path is not None and bundle is None:
        raise PrepareError("the publication needs --bundle and --manifest together")

    updates = version_updates(root, version, tag)
    for path, _ in updates:
        relative = path.relative_to(root).as_posix()
        if dry_run:
            print(f"would change {relative}")
    if not dry_run:
        for path, text in updates:
            path.write_text(text, encoding="utf-8", newline="\n")

    if bundle is not None and manifest_path is not None:
        manifest = read_manifest(manifest_path)
        if dry_run:
            print(f"would publish {len(manifest)} schema files to {published}")
        else:
            published_paths = publish_bundle(bundle, manifest, published, tag)
            for relative_path in published_paths:
                print(f"published {relative_path}")

    if dry_run:
        print("dry run: nothing was written")
        return 0

    problems = verify_release(
        root,
        tag,
        bundle=bundle,
        manifest_path=manifest_path,
        published=published,
    )
    for problem in problems:
        print(f"typcast-prepare-release: error: {problem}", file=sys.stderr)
    if problems:
        return 1

    print("every manifest, every schema source, and the changelog agree with "
          f"{tag}")
    if bundle is not None and manifest_path is not None:
        print("the published bundle matches the build")
        print("the archive of the published bundle matches the archive of the build")

    print(f"prepared {tag}")
    print(f"next: git add -A && git commit -m \"release: {tag}\"")
    print(f"next: git tag {tag}")
    return 0


def clean_published_bundle(
    tag: str,
    published: Path,
    manifest_path: Path | None,
    dry_run: bool = False,
) -> int:
    """Removes the generated published files and returns the exit code."""
    if manifest_path is None:
        raise PrepareError("the cleanup needs --manifest")

    removed = clean_release(published, manifest_path, dry_run=dry_run)
    for relative_path in removed:
        if dry_run:
            print(f"would remove {relative_path}")
        else:
            print(f"removed {relative_path}")

    if dry_run:
        print("dry run: nothing was written")
        return 0

    print(f"cleaned the published bundle of {tag}")
    print(
        'next: git add -A && git commit -m '
        '"chore(release): remove the generated published bundle"'
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="typcast-prepare-release",
        description="Prepare the release commit of a Typcast release.",
    )
    parser.add_argument(
        "--version",
        required=True,
        help="Release tag, for example v1.0.0.",
    )
    parser.add_argument(
        "--root",
        default=None,
        help="Repository root. The current directory by default.",
    )
    parser.add_argument(
        "--bundle",
        type=Path,
        default=None,
        help="Built schema bundle directory.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Manifest of the bundle files.",
    )
    parser.add_argument(
        "--published",
        type=Path,
        default=None,
        help="Directory that holds the published bundle. `specs/schemas` by default.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report the changes without writing them.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the generated published files after the release.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        root = find_root(args.root)
        return prepare(
            root,
            args.version,
            bundle=args.bundle,
            manifest_path=args.manifest,
            published=args.published,
            dry_run=args.dry_run,
            clean=args.clean,
        )
    except (PrepareError, PublishError) as error:
        print(f"typcast-prepare-release: error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
