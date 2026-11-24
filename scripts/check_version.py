"""Check that a release version agrees across the manifests and the changelog.

The release gate runs before a tag is created and again in the release lane.
Every manifest carries the version of the release, and the changelog carries
the entry of the release. A mismatch fails the release.

The script uses the Python standard library only, so it needs no SDK
installation and no network access.

Usage:

    python scripts/check_version.py --version v1.0.0 [--root PATH]

`--version` accepts a release tag such as `v1.0.0` or a plain version such
as `1.0.0`. `--root` points at the repository root. Without it, the script
locates the root in the current directory, in a Bazel runfiles tree, or next
to the script.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from pathlib import Path

VERSION_RE = re.compile(r"^v?(\d+\.\d+\.\d+)$")
MODULE_VERSION_RE = re.compile(r"module\s*\((.*?)\)", re.S)
MODULE_FIELD_RE = re.compile(r'version\s*=\s*"([^"]+)"')
CHANGELOG_VERSION_RE = re.compile(r"^##\s+\[?(\d+\.\d+\.\d+)\]?", re.M)

# The files that carry the version of the release.
MANIFESTS = (
    ("MODULE.bazel", "the Bazel module"),
    ("package.json", "the workspace manifest"),
    ("packages/python/pyproject.toml", "the Python package manifest"),
    ("packages/typescript/package.json", "the TypeScript package manifest"),
)
CHANGELOG = "CHANGELOG.md"


def find_root(explicit: str | None) -> Path:
    """Locates the repository root in a checkout and in a Bazel runfiles tree."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit).resolve())
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
    candidates.append(Path(__file__).resolve().parents[1])
    for candidate in candidates:
        if (candidate / "MODULE.bazel").is_file() and (candidate / CHANGELOG).is_file():
            return candidate
    raise SystemExit("repository root not found; pass --root")


def module_version(path: Path) -> str | None:
    """Returns the version of the `module` block of a Bazel module file."""
    text = path.read_text(encoding="utf-8")
    match = MODULE_VERSION_RE.search(text)
    if not match:
        return None
    field = MODULE_FIELD_RE.search(match.group(1))
    return field.group(1) if field else None


def json_version(path: Path) -> str | None:
    """Returns the version of a JSON manifest."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(document, dict):
        return None
    version = document.get("version")
    return version if isinstance(version, str) else None


def pyproject_version(path: Path) -> str | None:
    """Returns the version of the project table of a `pyproject.toml` file."""
    try:
        document = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError:
        return None
    project = document.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    return version if isinstance(version, str) else None


def read_version(path: Path) -> str | None:
    """Returns the version of a manifest, whatever its format is."""
    if path.suffix == ".toml":
        return pyproject_version(path)
    if path.suffix == ".json":
        return json_version(path)
    return module_version(path)


def changelog_versions(path: Path) -> list[str]:
    """Returns the versions that the changelog has an entry for."""
    return CHANGELOG_VERSION_RE.findall(path.read_text(encoding="utf-8"))


def check_versions(root: Path, version: str) -> list[str]:
    """Returns one message per version mismatch.

    An empty list means that every manifest and the changelog agree with the
    release version.
    """
    match = VERSION_RE.match(version.strip())
    if not match:
        return [f"version must be a release tag such as v1.0.0, got {version!r}"]
    expected = match.group(1)

    problems: list[str] = []
    for relative_path, description in MANIFESTS:
        path = root / relative_path
        if not path.is_file():
            problems.append(f"missing {description}: {relative_path}")
            continue
        found = read_version(path)
        if found is None:
            problems.append(f"cannot read the version of {description}: {relative_path}")
        elif found != expected:
            problems.append(
                f"{description} has version {found}, expected {expected}: {relative_path}"
            )

    changelog = root / CHANGELOG
    if not changelog.is_file():
        problems.append(f"missing changelog: {CHANGELOG}")
    elif expected not in changelog_versions(changelog):
        problems.append(f"the changelog has no entry for {expected}: {CHANGELOG}")

    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", required=True, help="release tag, for example v1.0.0")
    parser.add_argument("--root", default=None, help="repository root")
    args = parser.parse_args(argv)

    root = find_root(args.root)
    problems = check_versions(root, args.version)
    for problem in problems:
        print(f"typcast-version: error: {problem}", file=sys.stderr)
    if problems:
        return 1
    print(f"every manifest and the changelog agree with {args.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
