"""Repository structure, dependency, and toolchain checks.

The script reads the source tree of the repository and reports the problems
that the rules of `docs/architecture/repository.md` and
`docs/development/build.md` must catch:

- Dependencies: `specs/` imports no SDK code, each SDK depends on no code
  outside itself, and the repository checks need no SDK installation.
- Packages: every Python package directory holds an `__init__.py`, and every
  Python test module is a complete program, so the build needs no
  `--test_filter`.
- Toolchain: the Python toolchain is hermetic and pinned, the lock file of the
  Bazel module is present, and the TypeScript compiler version comes from the
  root manifest.
- Decisions: every ADR uses the template of `docs/decisions/README.md`.
- Artifacts: the generated published schemas are committed only in a release
  commit.

The script uses the Python standard library only, so it needs no SDK
installation and no network access.

Usage:

    python scripts/check_repository.py [--root PATH]

`--root` points at the repository root. Without it, the script locates the
root in the current directory, in a Bazel runfiles tree, or next to the script.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

from check_version import check_versions, module_version, read_version

# The directories that the checks never read.
IGNORED_DIRECTORIES = {
    ".aspect",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}

# The package name of the Python SDK. The TypeScript SDK publishes the same
# name on npm, so the name also identifies the SDK in a TypeScript import.
SDK_PACKAGE = "typcast"

# The published schema files that the release commit adds to the source tree.
# They are build outputs, so the development branch must not carry them.
GENERATED_SCHEMA_DIRECTORY = "specs/schemas/api/types"

# The fields and the sections of the ADR template of `docs/decisions/README.md`.
ADR_FIELDS = ("Status:", "Date:", "Supersedes:", "Superseded by:")
ADR_SECTIONS = (
    "Context",
    "Decision",
    "Consequences",
    "Alternatives considered",
    "References",
)
ADR_TITLE_RE = re.compile(r"^# ADR-(\d{4}): \S")
ADR_DATE_RE = re.compile(r"^Date: (\d{4}-\d{2}-\d{2})$")

# The version of a manifest that must be exact, not a range.
EXACT_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+([-+].+)?$")

# The version constants that the SDKs export. The API of `docs/specifications/
# sdk-api.md` names them, and each of them must match the version of the
# manifest of its package.
PYTHON_VERSION_RE = re.compile(r'^__version__\s*=\s*"([^"]+)"', re.M)
TYPESCRIPT_VERSION_RE = re.compile(
    r'export\s+const\s+VERSION\s*=\s*"([^"]+)"',
)

# The version of Bazel that `.bazelversion` holds.
BAZEL_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")

# The suffixes of the files that belong to a Bazel package.
SOURCE_SUFFIXES = (".bzl", ".csv", ".py", ".tmpl", ".ts")

# The patterns that the ignore file must hold for the environment files.
GITIGNORE_PATTERNS = (".env", ".env.*")

# The dependency updates that Dependabot must open a pull request for. Every
# entry names the ecosystem of the manifest and the directory of the manifest.
DEPENDABOT_UPDATES = (
    ("bazel", "/"),
    ("npm", "/"),
    ("npm", "/packages/typescript"),
    ("pip", "/packages/python"),
)

# The pattern of one update block of the Dependabot configuration.
DEPENDABOT_ECOSYSTEM_RE = re.compile(r"^\s*-\s*package-ecosystem:\s*(\S+)\s*$")
DEPENDABOT_DIRECTORY_RE = re.compile(r"^\s*directory:\s*\"?([^\"\s]+)\"?\s*$")

# The imports of a TypeScript file. A module specifier follows `from`, or it
# is the target of a side effect import.
TS_FROM_RE = re.compile(r"""\bfrom\s*["']([^"']+)["']""")
TS_BARE_RE = re.compile(r"""^\s*import\s*["']([^"']+)["']""")


@dataclass
class Report:
    """Collects the problems that the checks find."""

    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warning(self, message: str) -> None:
        self.warnings.append(message)


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
        if (candidate / "MODULE.bazel").is_file() and (candidate / "docs").is_dir():
            return candidate
    raise SystemExit("repository root not found; pass --root")


def is_ignored(relative: Path) -> bool:
    """Returns whether a path belongs to a directory that the checks skip."""
    for part in relative.parts[:-1]:
        if part in IGNORED_DIRECTORIES or part.startswith("bazel-"):
            return True
    return False


def source_files(root: Path, suffix: str) -> list[Path]:
    """Returns the files of the repository that end with a suffix.

    The walk skips the ignored directories and does not follow the symbolic
    links of the Bazel output trees.
    """
    files: list[Path] = []
    for directory, subdirectories, names in os.walk(root):
        subdirectories[:] = [
            name
            for name in subdirectories
            if name not in IGNORED_DIRECTORIES and not name.startswith("bazel-")
        ]
        for name in names:
            if name.endswith(suffix):
                files.append(Path(directory) / name)
    return sorted(files)


def source_directories(root: Path, name: str) -> list[Path]:
    """Returns the directories of the repository that carry a given name.

    The walk skips the ignored directories and the Bazel output trees, so a
    build directory never becomes the owner of a module.
    """
    found: list[Path] = []
    for directory, subdirectories, _ in os.walk(root):
        subdirectories[:] = [
            entry
            for entry in subdirectories
            if entry not in IGNORED_DIRECTORIES and not entry.startswith("bazel-")
        ]
        candidate = Path(directory) / name
        if candidate.is_dir():
            found.append(candidate)
    return sorted(found)


def python_files(root: Path) -> list[Path]:
    """Returns the Python modules of the repository, in a stable order."""
    return source_files(root, ".py")


def package_directories(directory: Path, root: Path) -> list[Path]:
    """Returns the package directories of a module, outermost first.

    A directory is a package directory when it holds an `__init__.py`. The
    chain stops at the first directory that is not a package, because a module
    below it is not imported as a package member.
    """
    chain: list[Path] = []
    current = directory
    while current != root and current != current.parent:
        if not (current / "__init__.py").is_file():
            break
        chain.append(current)
        current = current.parent
    chain.reverse()
    return chain


def import_root(directory: Path, root: Path) -> Path:
    """Returns the directory that the import path of a module starts at.

    The import root is the directory that the build puts on the import path.
    It is the `src` directory of a distribution, or the outermost package
    directory of a package that is imported from its own directory.
    """
    chain = package_directories(directory, root)
    if not chain:
        return directory
    outermost = chain[0]
    parent = outermost.parent
    if parent != root and parent.name == "src":
        return parent
    return outermost


def module_name(path: Path, root: Path) -> str:
    """Returns the dotted name that the build imports a module under."""
    directory = path.parent
    root_directory = import_root(directory, root)
    parts = list(path.relative_to(root_directory).parts)
    parts[-1] = path.stem
    return ".".join(parts)


def imported_modules(path: Path) -> list[str]:
    """Returns the absolute module names that a Python file imports."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return []
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                names.append(node.module)
    return names


def typescript_imports(path: Path) -> list[str]:
    """Returns the module specifiers that a TypeScript file imports."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import") or stripped.startswith("export")):
            continue
        names.extend(TS_FROM_RE.findall(stripped))
        names.extend(TS_BARE_RE.findall(stripped))
    return names


def relative_to_root(path: Path, root: Path) -> str:
    """Returns the path of a file relative to the repository root."""
    return path.relative_to(root).as_posix()


def check_specs_dependencies(root: Path, report: Report) -> int:
    """Checks that `specs/` depends on no SDK code."""
    checked = 0
    directory = root / "specs"
    if not directory.is_dir():
        return 0
    for path in python_files(directory):
        checked += 1
        for name in imported_modules(path):
            if name.split(".")[0] == SDK_PACKAGE:
                report.error(
                    f"{relative_to_root(path, root)}: imports the SDK package "
                    f"'{name}'; specs/ must not depend on SDK code"
                )
    for path in source_files(directory, ".ts"):
        checked += 1
        for name in typescript_imports(path):
            if name.split("/")[0] == SDK_PACKAGE:
                report.error(
                    f"{relative_to_root(path, root)}: imports the SDK package "
                    f"'{name}'; specs/ must not depend on SDK code"
                )
    return checked


def check_sdk_isolation(root: Path, report: Report) -> int:
    """Checks that each SDK depends on no code outside itself."""
    checked = 0

    python_sdk = root / "packages" / "python"
    if python_sdk.is_dir():
        for path in python_files(python_sdk):
            checked += 1
            for name in imported_modules(path):
                owner = repository_module_owner(root, name)
                if owner is None:
                    continue
                if not owner.is_relative_to(python_sdk):
                    report.error(
                        f"{relative_to_root(path, root)}: imports '{name}' from "
                        f"{relative_to_root(owner, root)}; the Python SDK must "
                        "not depend on code outside itself, and the two SDKs "
                        "must not depend on each other"
                    )

    typescript_sdk = root / "packages" / "typescript"
    if typescript_sdk.is_dir():
        for path in source_files(typescript_sdk, ".ts"):
            checked += 1
            for name in typescript_imports(path):
                if not name.startswith("."):
                    continue
                target = (path.parent / name).resolve()
                if not target.is_relative_to(typescript_sdk.resolve()):
                    report.error(
                        f"{relative_to_root(path, root)}: imports '{name}', "
                        "which is outside the TypeScript SDK; the TypeScript "
                        "SDK must not depend on code outside itself, and the "
                        "two SDKs must not depend on each other"
                    )
    return checked


def repository_module_owner(root: Path, name: str) -> Path | None:
    """Returns the directory that owns a module of the repository.

    The owner is the import root of the module, so that a module of a package
    is owned by the distribution that holds it. A module that the repository
    does not hold has no owner.
    """
    parts = name.split(".")
    for path in python_files(root):
        if module_name(path, root) == name:
            return import_root(path.parent, root)
    for directory in source_directories(root, "src"):
        candidate = directory.joinpath(*parts).with_suffix(".py")
        if candidate.is_file():
            return directory
        package = directory.joinpath(*parts) / "__init__.py"
        if package.is_file():
            return directory
    return None


def check_gate_independence(root: Path, report: Report) -> int:
    """Checks that the repository checks need no SDK installation."""
    checked = 0
    directory = root / "scripts"
    if not directory.is_dir():
        return 0
    for path in python_files(directory):
        checked += 1
        for name in imported_modules(path):
            if name.split(".")[0] == SDK_PACKAGE:
                report.error(
                    f"{relative_to_root(path, root)}: imports the SDK package "
                    f"'{name}'; the repository checks must not need an SDK "
                    "installation"
                )
    return checked


def check_python_packages(root: Path, report: Report) -> int:
    """Checks that every Python package directory holds an `__init__.py`."""
    checked = 0
    roots: set[Path] = set()
    for path in python_files(root):
        directory = path.parent
        roots.add(import_root(directory, root))
        checked += 1

    for root_directory in sorted(roots):
        for directory in sorted(package_candidates(root_directory)):
            if not any(directory.glob("*.py")):
                continue
            if not (directory / "__init__.py").is_file():
                report.error(
                    f"{relative_to_root(directory, root)}: holds Python modules "
                    "but no __init__.py; a Python package directory must hold "
                    "an __init__.py"
                )
    return checked


def package_candidates(root_directory: Path) -> list[Path]:
    """Returns the directories below an import root that hold Python code."""
    candidates: list[Path] = []
    for path in sorted(root_directory.rglob("*")):
        if not path.is_dir():
            continue
        relative = path.relative_to(root_directory)
        if is_ignored(relative):
            continue
        candidates.append(path)
    return candidates


def check_test_modules(root: Path, report: Report) -> int:
    """Checks that every Python test module is a complete program.

    The `py_test` targets of the repository run a module as a program. A test
    module that is not a complete program would need a `--test_filter` to
    select its cases, and the build ignores that option.
    """
    checked = 0
    for path in python_files(root):
        if not is_test_module(path):
            continue
        checked += 1
        text = path.read_text(encoding="utf-8")
        if 'if __name__ == "__main__":' not in text:
            report.error(
                f"{relative_to_root(path, root)}: a test module must be a "
                'complete program with an \'if __name__ == "__main__":\' guard'
            )
    return checked


def is_test_module(path: Path) -> bool:
    """Returns whether a Python file is a test module."""
    if path.name == "__init__.py":
        return False
    if path.stem.startswith("test_"):
        return True
    return path.parent.name == "tests"


def check_toolchain(root: Path, report: Report) -> int:
    """Checks that the Python toolchain is hermetic and that the lock file is present."""
    checked = 0
    module_file = root / "MODULE.bazel"
    if not module_file.is_file():
        report.error("MODULE.bazel is missing")
        return checked
    text = module_file.read_text(encoding="utf-8")
    checked += 1

    defaults = re.search(r"python\.defaults\s*\((.*?)\)", text, re.S)
    toolchain = re.search(r"python\.toolchain\s*\((.*?)\)", text, re.S)
    if defaults is None:
        report.error("MODULE.bazel: python.defaults() is missing")
    if toolchain is None:
        report.error("MODULE.bazel: python.toolchain() is missing")

    versions = set()
    for name, match in (("python.defaults", defaults), ("python.toolchain", toolchain)):
        if match is None:
            continue
        version = re.search(r'python_version\s*=\s*"([^"]+)"', match.group(1))
        if version is None:
            report.error(f"MODULE.bazel: {name}() must pin a python_version")
            continue
        versions.add(version.group(1))
    if len(versions) > 1:
        report.error(
            "MODULE.bazel: python.defaults() and python.toolchain() pin "
            f"different versions: {sorted(versions)}"
        )

    for forbidden in ("system_python", "local_python"):
        if forbidden in text:
            report.error(
                f"MODULE.bazel: uses '{forbidden}'; the Python toolchain must "
                "be hermetic"
            )

    lock_file = root / "MODULE.bazel.lock"
    checked += 1
    if not lock_file.is_file():
        report.error("MODULE.bazel.lock is missing; the lock file must be committed")
    elif lock_file.stat().st_size == 0:
        report.error("MODULE.bazel.lock is empty; the lock file must be committed")
    else:
        tracked = git_tracks(root, "MODULE.bazel.lock")
        if tracked is False:
            report.error(
                "MODULE.bazel.lock is not tracked by git; the lock file must "
                "be committed"
            )
    return checked


def git_tracks(root: Path, relative_path: str) -> bool | None:
    """Returns whether git tracks a file, or None when git is unavailable."""
    if not (root / ".git").exists():
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", relative_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return False
    return True


def check_typescript_version(root: Path, report: Report) -> int:
    """Checks that the TypeScript compiler version comes from the root manifest."""
    checked = 0
    workspace_manifest = root / "package.json"
    sdk_manifest = root / "packages" / "typescript" / "package.json"
    module_file = root / "MODULE.bazel"

    if not workspace_manifest.is_file():
        report.error("package.json is missing")
        return checked
    checked += 1

    workspace = read_json(workspace_manifest)
    if workspace is None:
        report.error("package.json is not valid JSON")
        return checked
    dev_dependencies = workspace.get("devDependencies")
    version = None
    if isinstance(dev_dependencies, dict):
        candidate = dev_dependencies.get("typescript")
        if isinstance(candidate, str):
            version = candidate
    if version is None:
        report.error(
            "package.json: the root manifest must declare the TypeScript "
            "compiler in devDependencies"
        )
    elif not EXACT_VERSION_RE.match(version):
        report.error(
            f"package.json: the TypeScript compiler version must be exact, "
            f"got {version!r}"
        )

    if sdk_manifest.is_file():
        checked += 1
        sdk = read_json(sdk_manifest)
        if sdk is None:
            report.error("packages/typescript/package.json is not valid JSON")
        else:
            for section in ("dependencies", "devDependencies", "peerDependencies"):
                dependencies = sdk.get(section)
                if isinstance(dependencies, dict) and "typescript" in dependencies:
                    report.error(
                        "packages/typescript/package.json: declares the "
                        f"TypeScript compiler in {section}; the version comes "
                        "from the root manifest"
                    )

    if module_file.is_file():
        checked += 1
        text = module_file.read_text(encoding="utf-8")
        if not re.search(
            r"typescript\.deps\s*\((.*?)\)", text, re.S
        ) or 'version_from = "//:package.json"' not in text:
            report.error(
                "MODULE.bazel: typescript.deps() must read the compiler "
                'version from "//:package.json"'
            )
    return checked


def read_json(path: Path) -> dict | None:
    """Returns a JSON document, or None when it cannot be read."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return document if isinstance(document, dict) else None


def check_sdk_version(root: Path, report: Report) -> int:
    """Checks that the version that each SDK exports matches its manifest."""
    checked = 0
    sources = (
        (
            root / "packages" / "python" / "src" / "typcast" / "version.py",
            root / "packages" / "python" / "pyproject.toml",
            PYTHON_VERSION_RE,
            "the Python SDK",
        ),
        (
            root / "packages" / "typescript" / "src" / "version.ts",
            root / "packages" / "typescript" / "package.json",
            TYPESCRIPT_VERSION_RE,
            "the TypeScript SDK",
        ),
    )
    for source, manifest, pattern, description in sources:
        if not source.is_file() or not manifest.is_file():
            report.error(f"{description} has no version source")
            continue
        checked += 1
        expected = read_version(manifest)
        found = pattern.search(source.read_text(encoding="utf-8"))
        if expected is None:
            report.error(f"cannot read the version of {description}")
            continue
        if found is None:
            report.error(
                f"{description} does not export its version: {source.name}"
            )
            continue
        if found.group(1) != expected:
            report.error(
                f"{description} exports version {found.group(1)}, expected "
                f"{expected}: {source.relative_to(root).as_posix()}"
            )
    return checked


def check_python_import_path(root: Path, report: Report) -> int:
    """Checks that the Python import path of the SDK is `typcast`."""
    checked = 0
    manifest = root / "packages" / "python" / "pyproject.toml"
    if not manifest.is_file():
        report.error("packages/python/pyproject.toml is missing")
        return checked
    checked += 1
    try:
        document = tomllib.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, tomllib.TOMLDecodeError):
        report.error("packages/python/pyproject.toml is not valid TOML")
        return checked
    project = document.get("project")
    name = project.get("name") if isinstance(project, dict) else None
    if name != SDK_PACKAGE:
        report.error(
            f"packages/python/pyproject.toml: the project name must be "
            f"{SDK_PACKAGE!r}, got {name!r}"
        )
    package = root / "packages" / "python" / "src" / SDK_PACKAGE
    if not (package / "__init__.py").is_file():
        report.error(
            f"packages/python/src/{SDK_PACKAGE}/__init__.py is missing; the "
            f"import path must be {SDK_PACKAGE!r}"
        )
    return checked


def check_decision_template(root: Path, report: Report) -> int:
    """Checks that every ADR uses the template of the decision index."""
    directory = root / "docs" / "decisions"
    if not directory.is_dir():
        report.error("docs/decisions is missing")
        return 0
    count = 0
    for path in sorted(directory.glob("ADR-*.md")):
        count += 1
        relative = relative_to_root(path, root)
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        if not lines or ADR_TITLE_RE.match(lines[0]) is None:
            report.error(f"{relative}: the title must be '# ADR-NNNN: Title'")

        field_positions: list[int] = []
        for field in ADR_FIELDS:
            index = next(
                (number for number, line in enumerate(lines) if line.startswith(field)),
                None,
            )
            if index is None:
                report.error(f"{relative}: missing the '{field}' field")
                field_positions.append(-1)
                continue
            field_positions.append(index)
        if field_positions != sorted(field_positions):
            report.error(
                f"{relative}: the fields must appear in the order of the "
                "template: Status, Date, Supersedes, Superseded by"
            )

        for number, line in enumerate(lines):
            if line.startswith("Date:") and ADR_DATE_RE.match(line) is None:
                report.error(f"{relative}:{number + 1}: the date must be YYYY-MM-DD")

        section_positions: list[int] = []
        for section in ADR_SECTIONS:
            index = next(
                (
                    number
                    for number, line in enumerate(lines)
                    if line.strip() == f"## {section}"
                ),
                None,
            )
            if index is None:
                report.error(f"{relative}: missing the '## {section}' section")
                section_positions.append(-1)
                continue
            section_positions.append(index)
        if section_positions != sorted(section_positions):
            report.error(
                f"{relative}: the sections must appear in the order of the "
                "template: Context, Decision, Consequences, Alternatives "
                "considered, References"
            )
    return count


def check_bazel_packages(root: Path, report: Report) -> int:
    """Checks that every source file belongs to a Bazel package.

    The repository is a Bazel monorepo, so the root holds the manifests and
    the policy files, and every source file lives in a package of its own. A
    source file in the root package would be a file that no target owns.
    """
    checked = 0
    if not (root / "MODULE.bazel").is_file():
        report.error(
            "MODULE.bazel is missing; the repository must remain a Bazel module"
        )
    if not (root / "BUILD.bazel").is_file():
        report.error(
            "BUILD.bazel is missing; the repository must remain a Bazel package"
        )

    packages = {path.parent for path in source_files(root, ".bazel")}
    for suffix in SOURCE_SUFFIXES:
        for path in source_files(root, suffix):
            checked += 1
            directory = path.parent
            owners = [
                package for package in packages if directory.is_relative_to(package)
            ]
            if not owners:
                report.error(
                    f"{relative_to_root(path, root)}: is outside every Bazel "
                    "package; a source file must belong to the build"
                )
                continue
            owner = max(owners, key=lambda package: len(package.parts))
            if owner == root:
                report.error(
                    f"{relative_to_root(path, root)}: is in the root package; "
                    "source code must live in a package of its own"
                )
    return checked


def check_bazel_version(root: Path, report: Report) -> int:
    """Checks that Bazelisk uses the version of `.bazelversion`."""
    checked = 0
    version_file = root / ".bazelversion"
    if not version_file.is_file():
        report.error(
            ".bazelversion is missing; Bazelisk must use a pinned Bazel version"
        )
        return checked
    checked += 1
    version = version_file.read_text(encoding="utf-8").strip()
    if not BAZEL_VERSION_RE.match(version):
        report.error(f".bazelversion: '{version}' is not a Bazel version")

    workflow_directory = root / ".github" / "workflows"
    for path in sorted(workflow_directory.glob("*.y*ml")):
        checked += 1
        text = path.read_text(encoding="utf-8")
        if "USE_BAZEL_VERSION" in text:
            report.error(
                f"{relative_to_root(path, root)}: sets USE_BAZEL_VERSION; the "
                "Bazel version comes from .bazelversion"
            )
    return checked


def check_gitignore(root: Path, report: Report) -> int:
    """Checks that the ignore file covers the environment files."""
    path = root / ".gitignore"
    if not path.is_file():
        report.error(".gitignore is missing")
        return 0
    lines = {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    missing = [pattern for pattern in GITIGNORE_PATTERNS if pattern not in lines]
    if missing:
        report.error(
            f".gitignore: missing the patterns: {', '.join(missing)}; an "
            "environment file must never be committed"
        )
    return 1


def check_npm_package_name(root: Path, report: Report) -> int:
    """Checks that the npm package is named `typcast`."""
    path = root / "packages" / "typescript" / "package.json"
    if not path.is_file():
        report.error("packages/typescript/package.json is missing")
        return 0
    document = read_json(path)
    if document is None:
        report.error("packages/typescript/package.json is not valid JSON")
        return 1
    name = document.get("name")
    if name != SDK_PACKAGE:
        report.error(
            "packages/typescript/package.json: the package name must be "
            f"{SDK_PACKAGE!r}, got {name!r}"
        )
    return 1


def check_dependabot(root: Path, report: Report) -> int:
    """Checks that Dependabot watches every dependency manifest.

    The repository declares its dependencies in the module file of Bazel, in
    the root npm manifest, in the npm manifest of the TypeScript SDK, and in
    the Python manifest of the Python SDK. A manifest that no update covers
    would never receive a security update.
    """
    path = root / ".github" / "dependabot.yml"
    if not path.is_file():
        report.error(
            ".github/dependabot.yml: is missing; every dependency manifest "
            "must be covered by an update"
        )
        return 0

    updates: set[tuple[str, str]] = set()
    ecosystem: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = DEPENDABOT_ECOSYSTEM_RE.match(line)
        if match:
            ecosystem = match.group(1)
            continue
        match = DEPENDABOT_DIRECTORY_RE.match(line)
        if match and ecosystem is not None:
            updates.add((ecosystem, match.group(1)))
            ecosystem = None

    missing = [
        f"{ecosystem} in {directory}"
        for ecosystem, directory in DEPENDABOT_UPDATES
        if (ecosystem, directory) not in updates
    ]
    if missing:
        report.error(
            ".github/dependabot.yml: no update for: " + ", ".join(missing)
        )
    return 1


def check_security_policy(root: Path, report: Report) -> int:
    """Checks that the security policy names a private reporting channel."""
    path = root / "SECURITY.md"
    if not path.is_file():
        report.error("SECURITY.md is missing")
        return 0
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    if "## reporting a vulnerability" not in lowered:
        report.error(
            "SECURITY.md: missing the 'Reporting a vulnerability' section"
        )
    if "private" not in lowered or "advisory" not in lowered:
        report.error(
            "SECURITY.md: must name the private reporting channel of a "
            "vulnerability"
        )
    if "/issues/new" in text or "new issue" in lowered:
        report.error(
            "SECURITY.md: must not direct a reporter of a vulnerability to a "
            "public issue"
        )
    return 1


def check_scope_document(root: Path, report: Report) -> int:
    """Checks that the repository publishes a scope document."""
    path = root / "docs" / "product" / "vision-and-scope.md"
    if not path.is_file():
        report.error(
            "docs/product/vision-and-scope.md is missing; the repository must "
            "publish a scope document"
        )
        return 0
    readme = root / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        if "docs/product/vision-and-scope.md" not in text:
            report.error(
                "README.md: must link the scope document of the repository"
            )
    return 1


def check_generated_artifacts(root: Path, report: Report) -> int:
    """Checks that the generated published schemas are committed only in a release commit.

    A raw URL serves the files of the tagged commit, so the release commit
    publishes the built bundle under `specs/schemas/`. The development branch
    must not carry those build outputs.
    """
    directory = root / GENERATED_SCHEMA_DIRECTORY
    if not directory.is_dir():
        return 0
    present = sorted(path.name for path in directory.glob("*.json"))
    if not present:
        return 0

    module_file = root / "MODULE.bazel"
    version = module_version(module_file) if module_file.is_file() else None
    if version is None:
        report.error(
            f"{GENERATED_SCHEMA_DIRECTORY}: the generated schemas are "
            "committed, but the version of the release cannot be read"
        )
        return len(present)

    problems = check_versions(root, version)
    if problems:
        report.error(
            f"{GENERATED_SCHEMA_DIRECTORY}: the generated schemas are "
            "committed, but this is not a release commit: " + "; ".join(problems)
        )
    return len(present)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repository root")
    args = parser.parse_args(argv)

    root = find_root(args.root)
    report = Report()

    specs = check_specs_dependencies(root, report)
    sdk = check_sdk_isolation(root, report)
    gate = check_gate_independence(root, report)
    packages = check_python_packages(root, report)
    tests = check_test_modules(root, report)
    toolchain = check_toolchain(root, report)
    typescript = check_typescript_version(root, report)
    sdk_version = check_sdk_version(root, report)
    import_path = check_python_import_path(root, report)
    decisions = check_decision_template(root, report)
    artifacts = check_generated_artifacts(root, report)
    bazel_packages = check_bazel_packages(root, report)
    bazel_version = check_bazel_version(root, report)
    ignore_file = check_gitignore(root, report)
    npm_name = check_npm_package_name(root, report)
    dependabot = check_dependabot(root, report)
    security_policy = check_security_policy(root, report)
    scope = check_scope_document(root, report)

    print(f"spec files checked: {specs}")
    print(f"sdk files checked: {sdk}")
    print(f"gate files checked: {gate}")
    print(f"python modules checked: {packages}")
    print(f"test modules checked: {tests}")
    print(f"toolchain files checked: {toolchain}")
    print(f"typescript files checked: {typescript}")
    print(f"sdk versions checked: {sdk_version}")
    print(f"python import paths checked: {import_path}")
    print(f"decision records checked: {decisions}")
    print(f"generated schema files checked: {artifacts}")
    print(f"bazel packages checked: {bazel_packages}")
    print(f"bazel version files checked: {bazel_version}")
    print(f"ignore files checked: {ignore_file}")
    print(f"npm manifests checked: {npm_name}")
    print(f"dependency configurations checked: {dependabot}")
    print(f"security policies checked: {security_policy}")
    print(f"scope documents checked: {scope}")
    print(f"errors: {len(report.errors)}")
    for error in report.errors:
        print(f"ERROR {error}")
    print(f"warnings: {len(report.warnings)}")
    for warning in report.warnings:
        print(f"WARN {warning}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
