import json
import tempfile
import unittest
from pathlib import Path

from check_version import SCHEMA_SOURCES
from prepare_release import (
    PrepareError,
    changelog_problems,
    generated_files,
    prepare,
    version_updates,
)
from typcast_publish.archive import bundle_archive_bytes
from typcast_publish.errors import PublishError

# The paths of the published bundle, relative to the bundle directory.
BUNDLE_FILES = (
    "validator.schema.json",
    "definitions/bound.schema.json",
    "definitions/node.schema.json",
    "api/types/alignment.schema.json",
    "api/types/length.schema.json",
    "api/types/paper.schema.json",
)


def schema_document(version: str, relative_path: str) -> str:
    """Returns a schema file with the identity of the given version."""
    return (
        "{\n"
        '  "$schema": "https://json-schema.org/draft/2020-12/schema",\n'
        '  "$id": "https://raw.githubusercontent.com/zuudevs/typcast/'
        "v%s/specs/schemas/%s\",\n"
        '  "type": "object"\n'
        "}\n" % (version, relative_path)
    )


def write_repository(root: Path, version: str = "0.1.0") -> Path:
    """Writes a repository that carries the given version everywhere."""
    (root / "MODULE.bazel").write_text(
        'module(\n    name = "typcast",\n    version = "%s",\n)\n' % version,
        encoding="utf-8",
        newline="\n",
    )
    (root / "package.json").write_text(
        json.dumps({"name": "typcast-workspace", "version": version}) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    packages = root / "packages"
    (packages / "python").mkdir(parents=True, exist_ok=True)
    (packages / "typescript").mkdir(parents=True, exist_ok=True)
    (packages / "python" / "pyproject.toml").write_text(
        '[project]\nname = "typcast"\nversion = "%s"\n' % version,
        encoding="utf-8",
        newline="\n",
    )
    (packages / "typescript" / "package.json").write_text(
        json.dumps({"name": "@zuudevs/typcast", "version": version}) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [1.0.0] - 2026-11-25\n\n- The release.\n",
        encoding="utf-8",
        newline="\n",
    )
    for relative_path, _ in SCHEMA_SOURCES:
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            schema_document(version, Path(relative_path).name.replace(".tmpl", "")),
            encoding="utf-8",
            newline="\n",
        )
    return root


def write_bundle(root: Path, version: str = "0.1.0") -> tuple[Path, Path]:
    """Writes a built bundle and its manifest, and returns both paths."""
    bundle = root / "bundle"
    bundle.mkdir(parents=True, exist_ok=True)
    for relative_path in BUNDLE_FILES:
        path = bundle / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(schema_document(version, relative_path), encoding="utf-8", newline="\n")
    manifest = bundle / "schema_manifest.txt"
    manifest.write_text("\n".join(BUNDLE_FILES) + "\n", encoding="utf-8", newline="\n")
    return bundle, manifest


class PrepareReleaseTests(unittest.TestCase):
    """Checks the release preparation of the repository."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        write_repository(self.root)
        self.bundle, self.manifest = write_bundle(self.root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def prepare(self, **kwargs: object) -> int:
        """Runs the preparation: the versions, then the publication.

        The bundle is built after the version bump, because the build carries
        the identity of the sources.
        """
        arguments = {
            "root": self.root,
            "tag": "v1.0.0",
        }
        arguments.update(kwargs)
        code = prepare(**arguments)  # type: ignore[arg-type]
        if code != 0:
            return code
        write_bundle(self.root, "1.0.0")
        return prepare(
            root=self.root,
            tag="v1.0.0",
            bundle=self.bundle,
            manifest_path=self.manifest,
        )

    def test_the_manifests_receive_the_release_version(self) -> None:
        code = self.prepare()

        self.assertEqual(code, 0)
        self.assertIn('version = "1.0.0"', (self.root / "MODULE.bazel").read_text())
        self.assertEqual(
            json.loads((self.root / "package.json").read_text())["version"],
            "1.0.0",
        )
        self.assertIn(
            'version = "1.0.0"',
            (self.root / "packages" / "python" / "pyproject.toml").read_text(),
        )
        self.assertEqual(
            json.loads(
                (self.root / "packages" / "typescript" / "package.json").read_text()
            )["version"],
            "1.0.0",
        )

    def test_the_schema_sources_receive_the_tag_identity(self) -> None:
        code = self.prepare()

        self.assertEqual(code, 0)
        source = (
            self.root / "specs" / "schemas" / "definitions" / "node.schema.json"
        ).read_text()
        self.assertIn(
            "https://raw.githubusercontent.com/zuudevs/typcast/v1.0.0/specs/schemas/",
            source,
        )

    def test_the_published_bundle_carries_the_tag_identity(self) -> None:
        code = self.prepare()

        self.assertEqual(code, 0)
        published = (
            self.root / "specs" / "schemas" / "api" / "types" / "paper.schema.json"
        ).read_text()
        self.assertIn(
            "https://raw.githubusercontent.com/zuudevs/typcast/v1.0.0/"
            "specs/schemas/api/types/paper.schema.json",
            published,
        )

    def test_a_version_that_is_not_a_release_tag_is_refused(self) -> None:
        with self.assertRaises(PublishError):
            self.prepare(tag="main")

    def test_a_missing_changelog_entry_is_refused(self) -> None:
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n",
            encoding="utf-8",
            newline="\n",
        )

        with self.assertRaises(PrepareError):
            self.prepare()

    def test_the_changelog_problem_names_the_missing_entry(self) -> None:
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n",
            encoding="utf-8",
            newline="\n",
        )

        problems = changelog_problems(self.root, "1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("1.0.0", problems[0])

    def test_the_dry_run_writes_nothing(self) -> None:
        before = (self.root / "MODULE.bazel").read_text()

        code = prepare(
            root=self.root,
            tag="v1.0.0",
            dry_run=True,
        )

        self.assertEqual(code, 0)
        self.assertEqual((self.root / "MODULE.bazel").read_text(), before)

    def test_the_preparation_is_idempotent(self) -> None:
        self.assertEqual(self.prepare(), 0)

        updates = version_updates(self.root, "1.0.0", "v1.0.0")

        self.assertEqual(updates, [])

    def test_an_unexpected_published_file_is_reported(self) -> None:
        self.assertEqual(self.prepare(), 0)
        unexpected = (
            self.root
            / "specs"
            / "schemas"
            / "api"
            / "types"
            / "stale.schema.json"
        )
        unexpected.write_text("{}\n", encoding="utf-8", newline="\n")

        code = prepare(
            root=self.root,
            tag="v1.0.0",
            bundle=self.bundle,
            manifest_path=self.manifest,
        )

        self.assertEqual(code, 1)

    def test_a_source_without_an_identity_is_refused(self) -> None:
        target = self.root / "specs" / "schemas" / "validator.schema.json"
        target.write_text("{}\n", encoding="utf-8", newline="\n")

        with self.assertRaises(PrepareError):
            prepare(root=self.root, tag="v1.0.0")

    def test_the_archive_of_the_published_bundle_matches_the_build(self) -> None:
        self.assertEqual(self.prepare(), 0)

        manifest = self.manifest.read_text().split()
        published = self.root / "specs" / "schemas"

        self.assertEqual(
            bundle_archive_bytes(published, manifest),
            bundle_archive_bytes(self.bundle, manifest),
        )

    def test_the_bundle_without_a_manifest_is_refused(self) -> None:
        with self.assertRaises(PrepareError):
            prepare(root=self.root, tag="v1.0.0", bundle=self.bundle)

    def test_the_publication_needs_the_bundle_and_the_manifest(self) -> None:
        with self.assertRaises(PrepareError):
            prepare(root=self.root, tag="v1.0.0", manifest_path=self.manifest)

    def test_a_bundle_that_predates_the_version_bump_is_reported(self) -> None:
        code = prepare(root=self.root, tag="v1.0.0")

        self.assertEqual(code, 0)
        code = prepare(
            root=self.root,
            tag="v1.0.0",
            bundle=self.bundle,
            manifest_path=self.manifest,
        )

        self.assertEqual(code, 1)

    def test_the_cleanup_removes_the_generated_published_files(self) -> None:
        self.assertEqual(self.prepare(), 0)
        published = self.root / "specs" / "schemas"

        code = prepare(
            root=self.root,
            tag="v1.0.0",
            manifest_path=self.manifest,
            clean=True,
        )

        self.assertEqual(code, 0)
        self.assertFalse((published / "api" / "types" / "paper.schema.json").exists())
        self.assertTrue((published / "validator.schema.json").exists())
        self.assertTrue(
            (published / "definitions" / "node.schema.json").exists(),
        )

    def test_the_cleanup_needs_the_manifest(self) -> None:
        with self.assertRaises(PrepareError):
            prepare(root=self.root, tag="v1.0.0", clean=True)

    def test_the_cleanup_does_not_publish_a_bundle(self) -> None:
        with self.assertRaises(PrepareError):
            prepare(
                root=self.root,
                tag="v1.0.0",
                bundle=self.bundle,
                manifest_path=self.manifest,
                clean=True,
            )

    def test_the_cleanup_does_not_change_the_versions(self) -> None:
        self.assertEqual(self.prepare(), 0)
        before = (self.root / "MODULE.bazel").read_text()

        code = prepare(
            root=self.root,
            tag="v1.0.0",
            manifest_path=self.manifest,
            clean=True,
        )

        self.assertEqual(code, 0)
        self.assertEqual((self.root / "MODULE.bazel").read_text(), before)

    def test_the_cleanup_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.prepare(), 0)
        published = self.root / "specs" / "schemas" / "api" / "types"

        code = prepare(
            root=self.root,
            tag="v1.0.0",
            manifest_path=self.manifest,
            clean=True,
            dry_run=True,
        )

        self.assertEqual(code, 0)
        self.assertTrue((published / "paper.schema.json").exists())

    def test_the_generated_files_are_the_manifest_files_without_a_source(self) -> None:
        manifest = self.manifest.read_text().split()

        generated = generated_files(manifest)

        self.assertIn("api/types/paper.schema.json", generated)
        self.assertNotIn("validator.schema.json", generated)
        self.assertNotIn("definitions/node.schema.json", generated)


if __name__ == "__main__":
    unittest.main()
