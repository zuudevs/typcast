"""Rehearse the release commit against the real repository files.

The unit tests of the preparation use a synthetic repository. This test uses
the real manifests, the real schema sources, and the bundle that the build
produces, so that the path that the release lane runs is covered by
`bazel test //...` on every platform.

The test never writes into the checkout. It copies the files into a temporary
tree, prepares the release there, and checks the published bundle, the
archive, and the cleanup.
"""

import json
import os
import re
import shutil
import tempfile
import unittest
from datetime import date
from pathlib import Path

from check_version import CHANGELOG, MANIFESTS, SCHEMA_SOURCES, schema_versions
from prepare_release import clean_release, prepare
from typcast_publish.archive import bundle_archive_bytes
from typcast_publish.publisher import published_url, read_manifest

# The release tag that the rehearsal uses. The contract version of the schema
# sources is lockstep with the version of the release, so the rehearsal uses
# the contract version of the sources.
RELEASE_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


def runfiles_candidates() -> list[Path]:
    """Returns the directories that may hold the runfiles tree."""
    candidates: list[Path] = []
    workspace = os.environ.get("TEST_WORKSPACE")
    for variable in ("RUNFILES_DIR", "TEST_SRCDIR"):
        runfiles = os.environ.get(variable)
        if not runfiles:
            continue
        base = Path(runfiles)
        candidates.append(base)
        if workspace:
            candidates.append(base / workspace)
        candidates.append(base / "_main")
    cwd = Path.cwd()
    candidates.append(cwd)
    if workspace:
        candidates.append(cwd / workspace)
    candidates.extend(Path(__file__).resolve().parents)
    return candidates


def in_bazel_test() -> bool:
    """Returns whether the test runs inside a Bazel test action."""
    return bool(os.environ.get("RUNFILES_DIR") or os.environ.get("TEST_SRCDIR"))


def find_repository() -> Path | None:
    """Returns the directory that holds the manifests and the changelog."""
    for candidate in runfiles_candidates():
        if (candidate / "MODULE.bazel").is_file() and (candidate / CHANGELOG).is_file():
            return candidate
    return None


def find_bundle(repository: Path) -> tuple[Path, Path] | None:
    """Returns the built bundle and the path of its manifest."""
    candidates = [repository / "specs" / "schemas"]
    for candidate in runfiles_candidates():
        candidates.append(candidate / "bazel-bin" / "specs" / "schemas")
    for candidate in candidates:
        manifest = candidate / "schema_manifest.txt"
        if manifest.is_file() and (candidate / "validator.schema.json").is_file():
            return candidate, manifest
    return None


def copy_file(source: Path, target: Path) -> None:
    """Copies one file and creates the directory of the target."""
    if not source.is_file():
        raise FileNotFoundError(f"the file is missing: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


class ReleaseFlowTests(unittest.TestCase):
    """Rehearses the release commit with the files of the repository."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.tree = self.root / "tree"
        self.build = self.root / "build"

        self.repository = find_repository()
        found = find_bundle(self.repository) if self.repository else None
        if self.repository is None or found is None:
            if in_bazel_test():
                self.fail("the repository files were not found")
            self.skipTest("the repository files and the bundle require a Bazel build")

        self.bundle_source, self.manifest_source = found
        self.manifest = read_manifest(self.manifest_source)
        self.tag = self.release_tag()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def release_tag(self) -> str:
        """Returns the release tag of the rehearsal."""
        source = self.repository / SCHEMA_SOURCES[0][0]
        versions = schema_versions(source)
        if not versions:
            self.fail(f"the schema source has no contract version: {source}")
        version = versions[0]
        if not RELEASE_VERSION_RE.match(version):
            self.skipTest(f"the contract version is not a release version: {version}")
        return f"v{version}"

    def copy_repository(self) -> None:
        """Copies the manifests, the changelog, and the schema sources."""
        copy_file(self.repository / CHANGELOG, self.tree / CHANGELOG)
        for relative_path, _ in MANIFESTS:
            copy_file(self.repository / relative_path, self.tree / relative_path)
        for relative_path, _ in SCHEMA_SOURCES:
            source = self.repository / relative_path
            if not source.is_file():
                # The bundle stages the tracked schemas. The staged file has
                # the same content as the source.
                source = self.bundle_source / Path(relative_path).relative_to(
                    "specs/schemas"
                )
            copy_file(source, self.tree / relative_path)

    def copy_bundle(self) -> Path:
        """Copies the built bundle and returns the path of the manifest."""
        for relative_path in self.manifest:
            copy_file(
                self.bundle_source / relative_path,
                self.build / relative_path,
            )
        manifest = self.build / "schema_manifest.txt"
        manifest.write_text(
            "\n".join(self.manifest) + "\n", encoding="utf-8", newline="\n"
        )
        return manifest

    def add_changelog_entry(self) -> None:
        """Adds the changelog entry of the rehearsal."""
        changelog = self.tree / CHANGELOG
        text = changelog.read_text(encoding="utf-8")
        today = date.today().isoformat()
        entry = f"## [{self.tag[1:]}] - {today}\n\n- The rehearsal.\n"
        text = text.replace("## [Unreleased]\n", "## [Unreleased]\n\n" + entry, 1)
        changelog.write_text(text, encoding="utf-8", newline="\n")

    def prepare_release(self) -> int:
        """Runs the preparation: the versions, then the publication."""
        self.copy_repository()
        self.add_changelog_entry()

        code = prepare(root=self.tree, tag=self.tag)
        if code != 0:
            return code

        manifest = self.copy_bundle()
        return prepare(
            root=self.tree,
            tag=self.tag,
            bundle=self.build,
            manifest_path=manifest,
        )

    def test_the_preparation_publishes_the_bundle_of_the_build(self) -> None:
        code = self.prepare_release()

        self.assertEqual(code, 0)

    def test_the_published_files_carry_the_release_identity(self) -> None:
        self.assertEqual(self.prepare_release(), 0)
        published = self.tree / "specs" / "schemas"

        for relative_path in self.manifest:
            document = json.loads(
                (published / relative_path).read_text(encoding="utf-8")
            )
            self.assertEqual(
                document["$id"],
                published_url(self.tag, relative_path),
                relative_path,
            )

    def test_the_published_tree_holds_the_bundle_files_only(self) -> None:
        self.assertEqual(self.prepare_release(), 0)
        published = self.tree / "specs" / "schemas"

        found = sorted(
            path.relative_to(published).as_posix()
            for path in published.rglob("*.json")
        )

        self.assertEqual(found, sorted(self.manifest))

    def test_the_archive_of_the_published_bundle_matches_the_build(self) -> None:
        self.assertEqual(self.prepare_release(), 0)
        published = self.tree / "specs" / "schemas"

        self.assertEqual(
            bundle_archive_bytes(published, self.manifest),
            bundle_archive_bytes(self.build, self.manifest),
        )

    def test_the_manifests_carry_the_release_version(self) -> None:
        self.assertEqual(self.prepare_release(), 0)

        for relative_path, _ in MANIFESTS:
            text = (self.tree / relative_path).read_text(encoding="utf-8")
            self.assertIn(self.tag[1:], text, relative_path)

    def test_the_cleanup_removes_the_generated_published_files(self) -> None:
        self.assertEqual(self.prepare_release(), 0)
        published = self.tree / "specs" / "schemas"
        manifest = self.build / "schema_manifest.txt"

        removed = clean_release(published, manifest)

        self.assertTrue(removed)
        for relative_path in self.manifest:
            if relative_path.startswith("api/types/"):
                self.assertFalse((published / relative_path).exists(), relative_path)
            else:
                self.assertTrue((published / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
