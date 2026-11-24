import json
import tempfile
import unittest
from pathlib import Path

from check_version import (
    MANIFESTS,
    changelog_versions,
    check_versions,
    find_root,
    read_version,
)


def write_repository(root: Path, version: str = "1.0.0") -> Path:
    """Writes a repository that carries the given version everywhere."""
    (root / "MODULE.bazel").write_text(
        'module(\n    name = "typcast",\n    version = "%s",\n)\n' % version,
        encoding="utf-8",
    )
    (root / "package.json").write_text(
        json.dumps({"name": "typcast-workspace", "version": version}) + "\n",
        encoding="utf-8",
    )
    packages = root / "packages"
    (packages / "python").mkdir(parents=True, exist_ok=True)
    (packages / "typescript").mkdir(parents=True, exist_ok=True)
    (packages / "python" / "pyproject.toml").write_text(
        '[project]\nname = "typcast"\nversion = "%s"\n' % version,
        encoding="utf-8",
    )
    (packages / "typescript" / "package.json").write_text(
        json.dumps({"name": "@zuudevs/typcast", "version": version}) + "\n",
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [Unreleased]\n\n## [%s] - 2026-11-24\n\n- The release.\n"
        % version,
        encoding="utf-8",
    )
    return root


class VersionCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_matching_versions_report_no_problem(self) -> None:
        write_repository(self.root)

        self.assertEqual(check_versions(self.root, "v1.0.0"), [])
        self.assertEqual(check_versions(self.root, "1.0.0"), [])

    def test_module_version_mismatch_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "MODULE.bazel").write_text(
            'module(\n    name = "typcast",\n    version = "0.9.0",\n)\n',
            encoding="utf-8",
        )

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("MODULE.bazel", problems[0])

    def test_workspace_manifest_mismatch_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "package.json").write_text(
            json.dumps({"name": "typcast-workspace", "version": "0.9.0"}) + "\n",
            encoding="utf-8",
        )

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("package.json", problems[0])

    def test_python_manifest_mismatch_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "packages" / "python" / "pyproject.toml").write_text(
            '[project]\nname = "typcast"\nversion = "0.9.0"\n',
            encoding="utf-8",
        )

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("pyproject.toml", problems[0])

    def test_typescript_manifest_mismatch_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "packages" / "typescript" / "package.json").write_text(
            json.dumps({"name": "@zuudevs/typcast", "version": "0.9.0"}) + "\n",
            encoding="utf-8",
        )

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("packages/typescript/package.json", problems[0])

    def test_missing_changelog_entry_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "CHANGELOG.md").write_text(
            "# Changelog\n\n## [Unreleased]\n\n- Work in progress.\n",
            encoding="utf-8",
        )

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("changelog", problems[0])

    def test_missing_manifest_is_reported(self) -> None:
        write_repository(self.root)
        (self.root / "packages" / "typescript" / "package.json").unlink()

        problems = check_versions(self.root, "v1.0.0")

        self.assertEqual(len(problems), 1)
        self.assertIn("packages/typescript/package.json", problems[0])

    def test_a_version_that_is_not_a_release_tag_is_reported(self) -> None:
        write_repository(self.root)

        problems = check_versions(self.root, "main")

        self.assertEqual(len(problems), 1)
        self.assertIn("release tag", problems[0])

    def test_changelog_versions_are_read_from_the_headings(self) -> None:
        write_repository(self.root)

        self.assertEqual(changelog_versions(self.root / "CHANGELOG.md"), ["1.0.0"])

    def test_the_repository_manifests_carry_the_same_version(self) -> None:
        root = find_root(None)

        versions = {
            relative_path: read_version(root / relative_path)
            for relative_path, _ in MANIFESTS
        }

        self.assertEqual(len(set(versions.values())), 1, versions)
        self.assertIsNotNone(next(iter(versions.values())))


if __name__ == "__main__":
    unittest.main()
