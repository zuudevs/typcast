"""Publish a built schema bundle under the identity of a release tag.

The published bundle is the file set that the tagged release commit carries
under `specs/schemas/`. Every published file keeps its relative path and
receives the absolute identity of its versioned raw URL, so a relative `$ref`
resolves to a sibling file at the same pinned tag.

The file set comes from the bundle manifest, not from a directory scan, because
the build directory also holds the outputs of other rules.

See `docs/decisions/ADR-0022-release-artifacts-schema-distribution-and-response-policy.md`.
"""

import json
import re
from pathlib import Path
from typing import Any

from typcast_publish.errors import PublishError

REPOSITORY = "zuudevs/typcast"
PUBLISHED_BASE = f"https://raw.githubusercontent.com/{REPOSITORY}/"
SCHEMA_ROOT = "specs/schemas"
RELEASE_TAG = re.compile(r"^v\d+\.\d+\.\d+$")


def validate_version(version: str) -> str:
    """Returns the version when it is a release tag, and raises otherwise.

    A `main` URL is a development reference. It is never a stable contract
    identity, so it is not a publishable version.
    """
    if not RELEASE_TAG.match(version):
        raise PublishError(
            f"version must be a release tag such as v1.0.0, got {version!r}; "
            "a main URL is a development reference only"
        )
    return version


def published_url(version: str, relative_path: str) -> str:
    """Returns the published URL of a schema file."""
    validate_version(version)
    return f"{PUBLISHED_BASE}{version}/{SCHEMA_ROOT}/{relative_path}"


def render_json_document(value: Any) -> str:
    """Render a Python JSON value the way the generator does."""
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    ) + "\n"


def write_manifest(relative_paths: list[str], output: Path) -> None:
    """Writes the bundle manifest: one relative path per line."""
    if not relative_paths:
        raise PublishError("the bundle manifest is empty")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        "\n".join(sorted(relative_paths)) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def read_manifest(path: Path) -> list[str]:
    """Reads the bundle manifest and returns the relative paths."""
    if not path.is_file():
        raise PublishError(f"bundle manifest not found: {path}")
    relative_paths = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not relative_paths:
        raise PublishError(f"bundle manifest is empty: {path}")
    return relative_paths


def bundle_files(bundle_dir: Path, manifest: list[str]) -> list[tuple[str, Path]]:
    """Returns the relative path and the path of every schema file."""
    if not bundle_dir.is_dir():
        raise PublishError(f"schema bundle not found: {bundle_dir}")

    files: list[tuple[str, Path]] = []
    for relative_path in manifest:
        path = bundle_dir / relative_path
        if not path.is_file():
            raise PublishError(
                f"schema bundle is incomplete: {relative_path} is missing"
            )
        files.append((relative_path, path))
    return files


def publish_document(document: Any, version: str, relative_path: str) -> str:
    """Returns the published text of one schema file."""
    if not isinstance(document, dict):
        raise PublishError(f"{relative_path}: a schema file must be a JSON object")

    published: dict[str, Any] = {}
    if "$schema" in document:
        published["$schema"] = document["$schema"]
    published["$id"] = published_url(version, relative_path)
    for key, value in document.items():
        if key not in ("$schema", "$id"):
            published[key] = value
    return render_json_document(published)


def publish_bundle(
    bundle_dir: Path,
    manifest: list[str],
    output_dir: Path,
    version: str,
) -> list[str]:
    """Writes the published bundle and returns the published relative paths."""
    validate_version(version)
    published_paths: list[str] = []

    for relative_path, path in bundle_files(bundle_dir, manifest):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PublishError(f"{relative_path}: invalid JSON: {error}") from error

        target = output_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            publish_document(document, version, relative_path),
            encoding="utf-8",
            newline="\n",
        )
        published_paths.append(relative_path)

    return published_paths


def check_published_bundle(
    bundle_dir: Path,
    manifest: list[str],
    published_dir: Path,
    version: str,
) -> list[str]:
    """Compares the published bundle with the built bundle.

    Returns one message per difference. An empty list means that the published
    bundle is the built bundle with the identity of the release tag.
    """
    validate_version(version)
    problems: list[str] = []

    expected: dict[str, str] = {}
    for relative_path, path in bundle_files(bundle_dir, manifest):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise PublishError(f"{relative_path}: invalid JSON: {error}") from error
        expected[relative_path] = publish_document(document, version, relative_path)

    if not published_dir.is_dir():
        return [f"published bundle not found: {published_dir}"]

    for relative_path, text in sorted(expected.items()):
        target = published_dir / relative_path
        if not target.is_file():
            problems.append(f"missing published file: {relative_path}")
            continue
        if target.read_text(encoding="utf-8") != text:
            problems.append(f"published file differs from the build: {relative_path}")

    for path in sorted(published_dir.rglob("*.json")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(published_dir).as_posix()
        if relative_path not in expected:
            problems.append(f"unexpected published file: {relative_path}")

    return problems
