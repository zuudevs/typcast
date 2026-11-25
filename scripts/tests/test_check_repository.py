"""Unit tests of the repository structure checks.

The tests build a synthetic repository for every case, so that every rule of
the checks is exercised without touching the checkout of the repository.
"""

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from check_repository import (
    Report,
    check_decision_template,
    check_gate_independence,
    check_generated_artifacts,
    check_python_import_path,
    check_python_packages,
    check_sdk_isolation,
    check_specs_dependencies,
    check_test_modules,
    check_toolchain,
    check_typescript_version,
)

MODULE_BAZEL = """module(
    name = "typcast",
    version = "0.1.0",
)

bazel_dep(
    name = "rules_python",
    version = "2.5.1",
)

python = use_extension(
    "@rules_python//python/extensions:python.bzl",
    "python",
)

python.defaults(
    python_version = "3.14",
)

python.toolchain(
    python_version = "3.14",
)

typescript = use_extension(
    "@aspect_rules_ts//ts:extensions.bzl",
    "typescript",
    dev_dependency = True,
)

typescript.deps(
    version_from = "//:package.json",
)
"""

WORKSPACE_MANIFEST = {
    "name": "typcast-workspace",
    "private": True,
    "version": "0.1.0",
    "devDependencies": {"typescript": "5.9.3"},
}

SDK_MANIFEST = {
    "name": "@zuudevs/typcast",
    "version": "0.1.0",
    "private": True,
    "type": "module",
}

PYPROJECT = """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "typcast"
version = "0.1.0"
description = "The Python SDK of Typcast."
requires-python = ">=3.11"
dependencies = []
"""

CHANGELOG = "# Changelog\n\n## [Unreleased]\n"

ADR = """# ADR-0001: A decision

Status: Accepted
Date: 2026-11-24
Supersedes: none
Superseded by: none

## Context

The context of the decision.

## Decision

The decision.

## Consequences

The consequences of the decision.

## Alternatives considered

The alternatives that were rejected.

## References

The references of the decision.
"""

SCHEMA_ID = (
    "https://raw.githubusercontent.com/zuudevs/typcast/v0.1.0/specs/schemas/"
)


def write(path: Path, text: str) -> None:
    """Writes a file and creates the directory of the file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def write_json(path: Path, document: object) -> None:
    """Writes a JSON document."""
    write(path, json.dumps(document, indent=2) + "\n")


def make_repository(root: Path) -> Path:
    """Builds a repository that satisfies every rule of the checks."""
    write(root / "MODULE.bazel", MODULE_BAZEL)
    write(root / "MODULE.bazel.lock", "{}\n")
    write_json(root / "package.json", WORKSPACE_MANIFEST)
    write(root / "CHANGELOG.md", CHANGELOG)

    write(root / "packages" / "python" / "pyproject.toml", PYPROJECT)
    write(root / "packages" / "python" / "src" / "typcast" / "__init__.py", "")
    write_json(root / "packages" / "typescript" / "package.json", SDK_MANIFEST)
    write(
        root / "packages" / "typescript" / "src" / "index.ts",
        "export const version = '0.1.0';\n",
    )

    write(root / "scripts" / "__init__.py", "")
    write(root / "scripts" / "validate_docs.py", '"""The gate."""\n')
    write(root / "scripts" / "tests" / "__init__.py", "")
    write(
        root / "scripts" / "tests" / "test_gate.py",
        '"""The tests."""\n\n\nif __name__ == "__main__":\n    pass\n',
    )

    write(root / "tools" / "publish" / "src" / "typcast_publish" / "__init__.py", "")
    write(
        root / "tools" / "publish" / "src" / "typcast_publish" / "publisher.py",
        '"""The publisher."""\n',
    )

    write(root / "specs" / "schemas" / "schema_tests.py", '"""The tests."""\n')
    write_json(
        root / "specs" / "schemas" / "validator.schema.json",
        {"$id": SCHEMA_ID + "validator.schema.json"},
    )
    write_json(
        root / "specs" / "schemas" / "definitions" / "bound.schema.json",
        {"$id": SCHEMA_ID + "definitions/bound.schema.json"},
    )
    write_json(
        root / "specs" / "schemas" / "definitions" / "node.schema.json",
        {"$id": SCHEMA_ID + "definitions/node.schema.json"},
    )
    for name in ("alignment", "length", "paper"):
        write(
            root
            / "specs"
            / "schemas"
            / "templates"
            / "api"
            / "types"
            / f"{name}.schema.json.tmpl",
            json.dumps({"$id": SCHEMA_ID + f"api/types/{name}.schema.json"}) + "\n",
        )

    write(root / "docs" / "decisions" / "ADR-0001-a-decision.md", ADR)
    return root


class RepositoryCheckTests(unittest.TestCase):
    """Exercises every rule of the repository checks."""

    def setUp(self) -> None:
        self.temporary_directory = TemporaryDirectory()
        self.root = make_repository(Path(self.temporary_directory.name))

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def run_check(self, check) -> Report:
        """Runs a check and returns its report."""
        report = Report()
        check(self.root, report)
        return report

    def test_a_valid_repository_has_no_problem(self) -> None:
        report = Report()
        check_specs_dependencies(self.root, report)
        check_sdk_isolation(self.root, report)
        check_gate_independence(self.root, report)
        check_python_packages(self.root, report)
        check_test_modules(self.root, report)
        check_toolchain(self.root, report)
        check_typescript_version(self.root, report)
        check_python_import_path(self.root, report)
        check_decision_template(self.root, report)
        check_generated_artifacts(self.root, report)

        self.assertEqual(report.errors, [])

    def test_a_specs_module_that_imports_the_sdk_is_reported(self) -> None:
        write(
            self.root / "specs" / "schemas" / "schema_tests.py",
            "import typcast\n",
        )

        report = self.run_check(check_specs_dependencies)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("must not depend on SDK code", report.errors[0])

    def test_a_specs_module_that_imports_a_tool_is_accepted(self) -> None:
        write(
            self.root / "specs" / "schemas" / "schema_tests.py",
            "import typcast_publish\n",
        )

        report = self.run_check(check_specs_dependencies)

        self.assertEqual(report.errors, [])

    def test_a_specs_typescript_file_that_imports_the_sdk_is_reported(self) -> None:
        write(
            self.root / "specs" / "schemas" / "helper.ts",
            'import { model } from "typcast";\n',
        )

        report = self.run_check(check_specs_dependencies)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("must not depend on SDK code", report.errors[0])

    def test_an_sdk_that_imports_the_other_sdk_is_reported(self) -> None:
        write(
            self.root / "packages" / "python" / "src" / "typcast" / "__init__.py",
            "from typcast_publish.publisher import publish\n",
        )

        report = self.run_check(check_sdk_isolation)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("must not depend on each other", report.errors[0])

    def test_an_sdk_that_imports_the_standard_library_is_accepted(self) -> None:
        write(
            self.root / "packages" / "python" / "src" / "typcast" / "__init__.py",
            "import json\nimport pathlib\n",
        )

        report = self.run_check(check_sdk_isolation)

        self.assertEqual(report.errors, [])

    def test_a_typescript_import_that_leaves_the_sdk_is_reported(self) -> None:
        write(
            self.root / "packages" / "typescript" / "src" / "index.ts",
            'export { helper } from "../../python/src/typcast";\n',
        )

        report = self.run_check(check_sdk_isolation)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("must not depend on each other", report.errors[0])

    def test_a_typescript_import_inside_the_sdk_is_accepted(self) -> None:
        write(
            self.root / "packages" / "typescript" / "src" / "helper.ts",
            "export const helper = 1;\n",
        )
        write(
            self.root / "packages" / "typescript" / "src" / "index.ts",
            'export { helper } from "./helper";\n',
        )

        report = self.run_check(check_sdk_isolation)

        self.assertEqual(report.errors, [])

    def test_a_gate_module_that_imports_the_sdk_is_reported(self) -> None:
        write(
            self.root / "scripts" / "validate_docs.py",
            "import typcast\n",
        )

        report = self.run_check(check_gate_independence)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("must not need an SDK installation", report.errors[0])

    def test_a_package_directory_without_an_init_file_is_reported(self) -> None:
        write(
            self.root / "packages" / "python" / "src" / "typcast" / "model" / "node.py",
            '"""The node."""\n',
        )

        report = self.run_check(check_python_packages)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("__init__.py", report.errors[0])

    def test_a_package_directory_with_an_init_file_is_accepted(self) -> None:
        write(
            self.root / "packages" / "python" / "src" / "typcast" / "model" / "node.py",
            '"""The node."""\n',
        )
        write(
            self.root
            / "packages"
            / "python"
            / "src"
            / "typcast"
            / "model"
            / "__init__.py",
            '"""The model."""\n',
        )

        report = self.run_check(check_python_packages)

        self.assertEqual(report.errors, [])

    def test_a_test_module_without_a_main_guard_is_reported(self) -> None:
        write(
            self.root / "scripts" / "tests" / "test_gate.py",
            '"""The tests."""\n',
        )

        report = self.run_check(check_test_modules)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("complete program", report.errors[0])

    def test_a_test_module_with_a_main_guard_is_accepted(self) -> None:
        report = self.run_check(check_test_modules)

        self.assertEqual(report.errors, [])

    def test_a_missing_lock_file_is_reported(self) -> None:
        (self.root / "MODULE.bazel.lock").unlink()

        report = self.run_check(check_toolchain)

        self.assertTrue(
            any("MODULE.bazel.lock is missing" in error for error in report.errors)
        )

    def test_an_empty_lock_file_is_reported(self) -> None:
        write(self.root / "MODULE.bazel.lock", "")

        report = self.run_check(check_toolchain)

        self.assertTrue(
            any("MODULE.bazel.lock is empty" in error for error in report.errors)
        )

    def test_a_missing_python_toolchain_is_reported(self) -> None:
        write(
            self.root / "MODULE.bazel",
            MODULE_BAZEL.replace(
                'python.toolchain(\n    python_version = "3.14",\n)\n', ""
            ),
        )

        report = self.run_check(check_toolchain)

        self.assertTrue(
            any("python.toolchain() is missing" in error for error in report.errors)
        )

    def test_a_system_python_toolchain_is_reported(self) -> None:
        write(
            self.root / "MODULE.bazel",
            MODULE_BAZEL.replace(
                'python.toolchain(\n    python_version = "3.14",\n)',
                'python.toolchain(\n    python_version = "3.14",\n'
                "    system_python = True,\n)",
            ),
        )

        report = self.run_check(check_toolchain)

        self.assertTrue(
            any("must be hermetic" in error for error in report.errors)
        )

    def test_a_different_default_and_toolchain_version_is_reported(self) -> None:
        write(
            self.root / "MODULE.bazel",
            MODULE_BAZEL.replace(
                'python.defaults(\n    python_version = "3.14",\n)',
                'python.defaults(\n    python_version = "3.11",\n)',
            ),
        )

        report = self.run_check(check_toolchain)

        self.assertTrue(
            any("different versions" in error for error in report.errors)
        )

    def test_a_missing_typescript_version_in_the_root_manifest_is_reported(self) -> None:
        write_json(self.root / "package.json", {"name": "typcast-workspace"})

        report = self.run_check(check_typescript_version)

        self.assertTrue(
            any("root manifest must declare" in error for error in report.errors)
        )

    def test_a_range_of_the_typescript_version_is_reported(self) -> None:
        document = dict(WORKSPACE_MANIFEST)
        document["devDependencies"] = {"typescript": "^5.9.3"}
        write_json(self.root / "package.json", document)

        report = self.run_check(check_typescript_version)

        self.assertTrue(
            any("must be exact" in error for error in report.errors)
        )

    def test_a_typescript_dependency_in_the_sdk_manifest_is_reported(self) -> None:
        document = dict(SDK_MANIFEST)
        document["devDependencies"] = {"typescript": "5.9.3"}
        write_json(self.root / "packages" / "typescript" / "package.json", document)

        report = self.run_check(check_typescript_version)

        self.assertTrue(
            any("version comes from the root manifest" in error for error in report.errors)
        )

    def test_a_module_that_does_not_read_the_root_manifest_is_reported(self) -> None:
        write(
            self.root / "MODULE.bazel",
            MODULE_BAZEL.replace(
                'typescript.deps(\n    version_from = "//:package.json",\n)',
                'typescript.deps(\n    version = "5.9.3",\n)',
            ),
        )

        report = self.run_check(check_typescript_version)

        self.assertTrue(
            any("must read the compiler version" in error for error in report.errors)
        )

    def test_a_wrong_python_project_name_is_reported(self) -> None:
        write(
            self.root / "packages" / "python" / "pyproject.toml",
            PYPROJECT.replace('name = "typcast"', 'name = "typecast"'),
        )

        report = self.run_check(check_python_import_path)

        self.assertTrue(
            any("the project name must be" in error for error in report.errors)
        )

    def test_a_missing_python_package_is_reported(self) -> None:
        (self.root / "packages" / "python" / "src" / "typcast" / "__init__.py").unlink()

        report = self.run_check(check_python_import_path)

        self.assertTrue(
            any("the import path must be" in error for error in report.errors)
        )

    def test_an_adr_without_a_section_is_reported(self) -> None:
        path = self.root / "docs" / "decisions" / "ADR-0001-a-decision.md"
        write(path, ADR.replace("## Alternatives considered", "## Other options"))

        report = self.run_check(check_decision_template)

        self.assertTrue(
            any("missing the '## Alternatives considered' section" in error
                for error in report.errors)
        )

    def test_an_adr_with_a_wrong_title_is_reported(self) -> None:
        path = self.root / "docs" / "decisions" / "ADR-0001-a-decision.md"
        write(path, ADR.replace("# ADR-0001: A decision", "ADR-0001 A decision"))

        report = self.run_check(check_decision_template)

        self.assertTrue(
            any("the title must be" in error for error in report.errors)
        )

    def test_an_adr_with_a_wrong_date_is_reported(self) -> None:
        path = self.root / "docs" / "decisions" / "ADR-0001-a-decision.md"
        write(path, ADR.replace("Date: 2026-11-24", "Date: 24.11.2026"))

        report = self.run_check(check_decision_template)

        self.assertTrue(
            any("the date must be YYYY-MM-DD" in error for error in report.errors)
        )

    def test_an_adr_with_the_fields_out_of_order_is_reported(self) -> None:
        path = self.root / "docs" / "decisions" / "ADR-0001-a-decision.md"
        write(
            path,
            ADR.replace(
                "Status: Accepted\nDate: 2026-11-24",
                "Date: 2026-11-24\nStatus: Accepted",
            ),
        )

        report = self.run_check(check_decision_template)

        self.assertTrue(
            any("must appear in the order of the template" in error
                for error in report.errors)
        )

    def test_generated_schemas_outside_a_release_commit_are_reported(self) -> None:
        write(
            self.root / "specs" / "schemas" / "api" / "types" / "alignment.schema.json",
            '{"$id": "' + SCHEMA_ID + 'api/types/alignment.schema.json"}\n',
        )

        report = self.run_check(check_generated_artifacts)

        self.assertEqual(len(report.errors), 1)
        self.assertIn("this is not a release commit", report.errors[0])

    def test_generated_schemas_in_a_release_commit_are_accepted(self) -> None:
        write(self.root / "CHANGELOG.md", "# Changelog\n\n## [0.1.0]\n\n- The release.\n")
        write(
            self.root / "specs" / "schemas" / "api" / "types" / "alignment.schema.json",
            '{"$id": "' + SCHEMA_ID + 'api/types/alignment.schema.json"}\n',
        )

        report = self.run_check(check_generated_artifacts)

        self.assertEqual(report.errors, [])


if __name__ == "__main__":
    unittest.main()
