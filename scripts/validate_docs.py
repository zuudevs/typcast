"""Repository documentation, requirement, and decision checks.

The script uses the Python standard library only, so the documentation gate
never depends on an SDK installation or on a network fetch. It reports the
problems that the gate in `docs/development/documentation.md` must catch:

- Encoding: UTF-8 without a byte order mark, LF line endings, a final newline.
- Text hygiene: no trailing whitespace, no tabs, no emoji, no replacement
  character, no mojibake.
- Markdown: one level-1 heading, code fences with a language, balanced fences,
  internal links that resolve.
- Requirements: unique IDs, an allowed status, family ranges that match the
  traceability index, and evidence for every implemented requirement.
- Decisions: an ADR index that lists every ADR, links that resolve, and
  supersede relations that point at a known ADR.
- Schema references: every published raw URL uses a path that exists in the
  repository, and no stale publishing domain is left in a current document.
- Schemas: valid JSON, and every relative `$ref` that resolves except the
  references that are documented as open defects.
- Workflows: every action is pinned to a commit SHA, every workflow declares
  its permissions, and no pull request workflow runs with write access or
  reads a secret.

Usage:

    python scripts/validate_docs.py [--root PATH] [--bundle PATH]

`--bundle` points at a built schema bundle, for example
`bazel-bin/specs/schemas`. The bundle check is skipped when it is not given.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote

FAMILIES = [
    "PRD", "UC", "AC", "UCR", "ARC", "REPO", "IR", "NODE", "SCH", "API",
    "EMIT", "COMP", "DIAG", "ASSET", "COMPAT", "BUILD", "TEST", "PERF",
    "CI", "REL", "SEC", "DOC", "GOV", "TRACE",
]
ALLOWED_STATUS = {"CONFIRMED", "IMPLEMENTED", "DEFERRED"}
REQUIREMENT_RE = re.compile(r"\b(" + "|".join(FAMILIES) + r")-(\d{3})\b")
DEFINITION_RE = re.compile(r"^\|\s*`?((?:" + "|".join(FAMILIES) + r")-(\d{3}))`?\s*\|")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
HEADING_RE = re.compile(r"^#\s+")
MOJIBAKE = [
    "\u00c3", "\u00c2", "\u00e2\u20ac\u2122", "\u00e2\u20ac\u0153",
    "\u00e2\u20ac\u009d", "\u00f0\u0178", "\u00ef\u00bf\u00bd",
]
EMOJI_RANGES = [
    (0x1F300, 0x1FAFF), (0x1F000, 0x1F2FF), (0x2600, 0x27BF),
    (0xFE00, 0xFE0F), (0x1F1E6, 0x1F1FF),
]
PLACEHOLDER_MARKERS = ("TODO", "TBD", "FIXME", "XXX", "???")
RAW_URL_RE = re.compile(
    r"https://raw\.githubusercontent\.com/zuudevs/typcast/"
    r"([^/\s`\"'()]+)/specs/schemas/([^\s`\"'()]+)"
)
OUTPUT_RE = re.compile(r'output\s*=\s*"([^"]+)"')
USES_RE = re.compile(r"^\s*(?:-\s+)?uses:\s*([^\s#]+)", re.M)
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
MERMAID_TYPES = (
    "flowchart", "graph", "sequenceDiagram", "classDiagram", "stateDiagram",
    "erDiagram", "journey", "gantt", "pie", "mindmap", "timeline",
)

# The historical records of the superseded decisions keep the old domain and
# the old placeholder identifier. They are the only documents that may do so.
LEGACY_DOMAIN_DOCUMENTS = {
    "docs/decisions/ADR-0020-release-artifact-and-response-policy.md",
    "docs/decisions/ADR-0021-schema-bundle-validation.md",
    "docs/decisions/ADR-0022-release-artifacts-schema-distribution-and-response-policy.md",
}

# References that do not resolve yet. Each entry names the defect that tracks
# it. An entry that becomes resolvable is reported so that it is removed.
KNOWN_UNRESOLVED_REFERENCES = {
    "api/types/paper.schema.json": "ADR-0023: generated schema, resolves in the built bundle.",
    "api/types/length.schema.json": "ADR-0023: generated schema, resolves in the built bundle.",
    "api/types/alignment.schema.json": "ADR-0023: generated schema, resolves in the built bundle.",
}


class Report:
    """Collects errors and warnings for one run."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
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
        if (candidate / "docs").is_dir() and (candidate / "README.md").is_file():
            return candidate
    raise SystemExit("repository root not found; pass --root")


def markdown_files(root: Path) -> list[Path]:
    files = [
        root / "README.md",
        root / "CHANGELOG.md",
        root / "CODE_OF_CONDUCT.md",
        root / "CONTRIBUTING.md",
        root / "SECURITY.md",
        root / "LICENSE",
        root / ".gitattributes",
        root / ".editorconfig",
        root / ".github" / "PULL_REQUEST_TEMPLATE.md",
    ]
    files.extend(sorted((root / "docs").rglob("*.md")))
    return [path for path in files if path.exists()]


def workflow_files(root: Path) -> list[Path]:
    """Returns the workflow files of the repository."""
    directory = root / ".github" / "workflows"
    if not directory.is_dir():
        return []
    return sorted(
        path
        for path in directory.iterdir()
        if path.is_file() and path.suffix in (".yml", ".yaml")
    )


def check_encoding(root: Path, files: list[Path], report: Report) -> None:
    for path in files:
        rel = path.relative_to(root).as_posix()
        data = path.read_bytes()
        if data.startswith(b"\xef\xbb\xbf"):
            report.error(f"{rel}: UTF-8 byte order mark")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError as exc:
            report.error(f"{rel}: invalid UTF-8: {exc}")
            continue
        if "\r\n" in text:
            report.error(f"{rel}: CRLF line endings")
        if data and not data.endswith(b"\n"):
            report.error(f"{rel}: missing final newline")
        if "\ufffd" in text:
            report.error(f"{rel}: replacement character")
        for pattern in MOJIBAKE:
            if pattern in text:
                report.error(f"{rel}: mojibake sequence U+{ord(pattern[0]):04X}")
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.rstrip(" \t") != line:
                report.error(f"{rel}:{lineno}: trailing whitespace")
            if "\t" in line:
                report.error(f"{rel}:{lineno}: tab character")
            for char in line:
                code = ord(char)
                if code < 128:
                    continue
                if any(start <= code <= end for start, end in EMOJI_RANGES):
                    report.error(f"{rel}:{lineno}: emoji or dingbat U+{code:04X}")
            if path.suffix == ".md":
                for marker in PLACEHOLDER_MARKERS:
                    if marker in line:
                        report.error(f"{rel}:{lineno}: placeholder marker {marker}")


def check_markdown(root: Path, files: list[Path], report: Report) -> None:
    for path in files:
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        if len(HEADING_RE.findall(text)) != 1:
            report.error(f"{rel}: expected exactly one level-1 heading")
        in_fence = False
        fence_language = ""
        fence_start = 0
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.startswith("```"):
                if not in_fence:
                    fence_language = line[3:].strip()
                    fence_start = lineno
                    if not fence_language:
                        report.error(f"{rel}:{lineno}: code fence without a language")
                    in_fence = True
                else:
                    in_fence = False
        if in_fence:
            report.error(f"{rel}:{fence_start}: unclosed code fence")
        for match in LINK_RE.finditer(text):
            target = match.group(1).strip()
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#", 1)[0])
            if not target:
                continue
            if not (path.parent / target).resolve().exists():
                report.error(f"{rel}: broken link {target}")


def check_mermaid(root: Path, files: list[Path], report: Report) -> None:
    for path in files:
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        in_mermaid = False
        body: list[str] = []
        start = 0
        for lineno, line in enumerate(lines, 1):
            if line.strip() == "```mermaid":
                in_mermaid = True
                body = []
                start = lineno
                continue
            if in_mermaid and line.strip() == "```":
                in_mermaid = False
                first = body[0].strip() if body else ""
                if not first.startswith(MERMAID_TYPES):
                    report.error(f"{rel}:{start}: Mermaid block does not start with a diagram type")
                if first.count("[") != first.count("]") or first.count('"') % 2:
                    report.error(f"{rel}:{start}: Mermaid block has unbalanced brackets or quotes")
                continue
            if in_mermaid:
                body.append(line)


def top_level_block(lines: list[str], key: str) -> list[str] | None:
    """Returns the lines of a top-level block, or None when it is absent.

    A block is either a key with indented lines below it or a key with its
    value on the same line.
    """
    for index, line in enumerate(lines):
        if line.startswith((" ", "\t")):
            continue
        stripped = line.strip()
        if not stripped.startswith(key):
            continue
        value = stripped[len(key):].strip()
        if value:
            return [value]
        block: list[str] = []
        for candidate in lines[index + 1:]:
            if candidate.strip() and not candidate.startswith((" ", "\t")):
                break
            block.append(candidate)
        return block
    return None


def is_pull_request_workflow(lines: list[str]) -> bool:
    """Returns whether the workflow runs for pull requests."""
    return any(line.strip() == "pull_request:" for line in lines)


def check_workflows(root: Path, files: list[Path], report: Report) -> int:
    """Checks the workflow files of the repository."""
    for path in files:
        rel = path.relative_to(root).as_posix()
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines()

        if not any(line.startswith("name:") for line in lines):
            report.error(f"{rel}: missing the workflow name")

        if "pull_request_target" in text:
            report.error(f"{rel}: pull_request_target runs the code of a fork")

        for match in USES_RE.finditer(text):
            reference = match.group(1)
            if reference.startswith("./") or reference.startswith("docker://"):
                continue
            if "@" not in reference:
                report.error(f"{rel}: action without a version: {reference}")
                continue
            commit = reference.partition("@")[2]
            if not COMMIT_SHA_RE.match(commit):
                report.error(f"{rel}: action is not pinned to a commit SHA: {reference}")

        permissions = top_level_block(lines, "permissions:")
        if permissions is None:
            report.error(f"{rel}: missing the permissions block")
        elif is_pull_request_workflow(lines):
            writes = [line.strip() for line in permissions if "write" in line]
            if writes:
                report.error(
                    f"{rel}: a pull request workflow grants write access: {writes[0]}"
                )

        if is_pull_request_workflow(lines) and "secrets." in text:
            report.error(f"{rel}: a pull request workflow reads a secret")

    return len(files)


def requirement_definitions(root: Path, files: list[Path]) -> dict[str, tuple[Path, int, str]]:
    """Returns the requirement definitions outside the traceability index."""
    definitions: dict[str, tuple[Path, int, str]] = {}
    index = root / "docs" / "requirements" / "traceability.md"
    for path in files:
        if path.suffix != ".md" or path == index:
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = DEFINITION_RE.match(line)
            if not match:
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            status = cells[2] if len(cells) > 2 else "MISSING"
            definitions[match.group(1)] = (path, lineno, status)
    return definitions


def check_requirements(root: Path, files: list[Path], report: Report) -> dict[str, str]:
    definitions = requirement_definitions(root, files)
    statuses: dict[str, str] = {}
    for req_id, (path, lineno, status) in sorted(definitions.items()):
        rel = path.relative_to(root).as_posix()
        if status not in ALLOWED_STATUS:
            report.error(f"{rel}:{lineno}: {req_id} has status {status}")
        statuses[req_id] = status

    lines = (root / "docs" / "requirements" / "traceability.md").read_text(encoding="utf-8").splitlines()

    declared: dict[str, tuple[int, int]] = {}
    in_families = False
    for line in lines:
        if line.startswith("## "):
            in_families = line.strip() == "## Requirement families"
            continue
        if not in_families:
            continue
        match = re.match(
            r"^\|\s*([^|]+?)\s*\|\s*`([^`]+)`\s*\|\s*`([A-Z]+)-(\d{3})`\s*to\s*`([A-Z]+)-(\d{3})`",
            line,
        )
        if match:
            declared[match.group(3)] = (int(match.group(4)), int(match.group(6)))

    for family, (low, high) in sorted(declared.items()):
        numbers = sorted(
            int(req_id.split("-")[1])
            for req_id in statuses
            if req_id.startswith(family + "-")
        )
        if not numbers:
            report.error(f"family {family}: declared range {low}-{high} has no requirements")
            continue
        gaps = sorted(set(range(low, high + 1)) - set(numbers))
        outside = sorted(set(numbers) - set(range(low, high + 1)))
        if gaps:
            report.error(f"family {family}: gaps in the declared range: {gaps}")
        if outside:
            report.error(f"family {family}: requirements outside the declared range: {outside}")
        if min(numbers) != low or max(numbers) != high:
            report.error(
                f"family {family}: declared {low}-{high}, actual {min(numbers)}-{max(numbers)}"
            )

    implemented = {req_id for req_id, status in statuses.items() if status == "IMPLEMENTED"}
    evidence: set[str] = set()
    in_evidence = False
    for line in lines:
        if line.startswith("## "):
            in_evidence = line.strip() == "## Implementation evidence"
            continue
        if in_evidence:
            match = DEFINITION_RE.match(line)
            if match:
                evidence.add(match.group(1))
    for req_id in sorted(implemented - evidence):
        report.error(f"{req_id} is IMPLEMENTED but has no implementation evidence")
    for req_id in sorted(evidence - implemented):
        report.error(f"{req_id} has implementation evidence but is not IMPLEMENTED")

    resolved: set[str] = set()
    in_resolved = False
    for line in lines:
        if line.startswith("## "):
            in_resolved = line.strip() == "## Resolved decisions"
            continue
        if in_resolved:
            match = DEFINITION_RE.match(line)
            if match:
                resolved.add(match.group(1))
    for req_id in sorted(resolved - set(statuses)):
        report.error(f"the resolved decisions table lists unknown requirement {req_id}")

    return statuses


def check_decisions(root: Path, report: Report) -> int:
    decision_dir = root / "docs" / "decisions"
    adr_files = sorted(decision_dir.glob("ADR-*.md"))
    statuses: dict[str, str] = {}
    superseded_by: dict[str, str] = {}
    supersedes: dict[str, str] = {}
    for path in adr_files:
        text = path.read_text(encoding="utf-8")
        number = path.name[:8]
        status_match = re.search(r"^Status:\s*(.+)$", text, re.M)
        superseded_match = re.search(r"^Superseded by:\s*(.+)$", text, re.M)
        supersedes_match = re.search(r"^Supersedes:\s*(.+)$", text, re.M)
        if not status_match:
            report.error(f"{path.name}: missing the Status field")
            continue
        statuses[number] = status_match.group(1).strip()
        superseded_by[number] = superseded_match.group(1).strip() if superseded_match else "none"
        supersedes[number] = supersedes_match.group(1).strip() if supersedes_match else "none"

    for path in adr_files:
        number = path.name[:8]
        if number not in statuses:
            continue
        if statuses[number] == "Superseded":
            target = superseded_by[number]
            if target not in statuses:
                report.error(f"{path.name}: superseded but 'Superseded by' is not a known ADR: {target}")
        if superseded_by[number] != "none" and superseded_by[number] not in statuses:
            report.error(f"{path.name}: 'Superseded by' points at an unknown ADR")
        target = supersedes[number]
        if target != "none" and target not in statuses:
            report.error(f"{path.name}: 'Supersedes' points at an unknown ADR: {target}")
        if statuses[number] == "Accepted" and target != "none" and statuses.get(target) != "Superseded":
            report.error(f"{path.name}: supersedes {target}, which is not marked Superseded")

    index_rows: dict[str, tuple[str, str]] = {}
    for line in (decision_dir / "README.md").read_text(encoding="utf-8").splitlines():
        match = re.match(
            r"^\|\s*\[(ADR-\d{4})\]\(([^)]+)\)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$",
            line,
        )
        if match:
            index_rows[match.group(1)] = (match.group(2), match.group(4).strip())
    for number in sorted(statuses):
        if number not in index_rows:
            report.error(f"{number}: missing from the ADR index")
    for number, (target, index_status) in sorted(index_rows.items()):
        if number not in statuses:
            report.error(f"the ADR index lists unknown ADR {number}")
            continue
        if not (decision_dir / target).exists():
            report.error(f"the ADR index link does not resolve: {target}")
        file_status = statuses[number]
        if file_status == "Accepted" and index_status != "Accepted":
            report.error(f"{number}: index status {index_status} does not match the file status")
        if file_status == "Superseded" and index_status != f"Superseded by {superseded_by[number]}":
            report.error(f"{number}: index status {index_status} does not name the superseding ADR")
    return len(adr_files)


def known_schema_paths(root: Path) -> set[str]:
    """Returns the schema paths relative to `specs/schemas`."""
    schema_root = root / "specs" / "schemas"
    paths = {
        path.relative_to(schema_root).as_posix()
        for path in schema_root.rglob("*")
        if path.is_file()
    }
    build_file = schema_root / "BUILD.bazel"
    if build_file.exists():
        for match in OUTPUT_RE.finditer(build_file.read_text(encoding="utf-8")):
            paths.add(match.group(1))
    return paths


def check_schema_references(root: Path, files: list[Path], report: Report) -> int:
    paths = known_schema_paths(root)
    urls: set[tuple[str, str]] = set()
    for path in files:
        if path.suffix != ".md":
            continue
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for match in RAW_URL_RE.finditer(line):
                version, schema_path = match.group(1), match.group(2)
                urls.add((version, schema_path))
                if schema_path == "<SCHEMA_FILE>":
                    continue
                if schema_path not in paths:
                    report.error(f"{rel}:{lineno}: raw URL path is not a repository path: {schema_path}")
                if version.startswith("v") and not re.match(r"^v\d+\.\d+\.\d+", version):
                    report.error(f"{rel}:{lineno}: raw URL version is not a release tag: {version}")
        if rel in LEGACY_DOMAIN_DOCUMENTS:
            continue
        text = path.read_text(encoding="utf-8")
        if "schemas.typcast.dev" in text:
            report.error(f"{rel}: stale schemas.typcast.dev reference")
        if "typcast.local" in text:
            report.error(f"{rel}: stale typcast.local placeholder reference")
    return len(urls)


def collect_references(document: object) -> list[str]:
    if isinstance(document, dict):
        references: list[str] = []
        for key, value in document.items():
            if key == "$ref" and isinstance(value, str):
                references.append(value)
            else:
                references.extend(collect_references(value))
        return references
    if isinstance(document, list):
        references = []
        for value in document:
            references.extend(collect_references(value))
        return references
    return []


def check_schema_files(root: Path, bundle: Path | None, report: Report) -> int:
    schema_root = root / "specs" / "schemas"
    checked = 0
    for path in sorted(schema_root.rglob("*.json")):
        rel = path.relative_to(root).as_posix()
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            report.error(f"{rel}: invalid JSON: {exc}")
            continue
        checked += 1
        for reference in collect_references(document):
            if reference.startswith(("#", "http://", "https://")):
                continue
            target = (path.parent / reference).resolve()
            relative = target.relative_to(schema_root.resolve()).as_posix() \
                if target.is_relative_to(schema_root.resolve()) else target.name
            if not target.exists():
                if relative not in KNOWN_UNRESOLVED_REFERENCES:
                    report.error(f"{rel}: unresolved reference {reference}")
            elif relative in KNOWN_UNRESOLVED_REFERENCES:
                report.warn(f"{rel}: reference {reference} resolves; remove its known-gap entry")

    if bundle is not None and bundle.exists():
        bundle_root = bundle.resolve()
        published = known_schema_paths(root)
        for path in sorted(bundle.rglob("*.json")):
            # A build directory also holds the runfiles tree of the bundle
            # test and the outputs of rules that no longer exist. Those copies
            # are not bundle files.
            if any(part.endswith(".runfiles") for part in path.relative_to(bundle).parts):
                continue
            rel = path.relative_to(bundle).as_posix()
            if rel not in published:
                report.warn(f"bundle {rel}: not a published schema path; ignored")
                continue
            try:
                document = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                report.error(f"bundle {rel}: invalid JSON: {exc}")
                continue
            checked += 1
            for reference in collect_references(document):
                if reference.startswith(("#", "http://", "https://")):
                    continue
                target = (path.parent / reference).resolve()
                if target.exists():
                    continue
                try:
                    relative = target.relative_to(bundle_root).as_posix()
                except ValueError:
                    relative = target.name
                if relative in KNOWN_UNRESOLVED_REFERENCES:
                    report.warn(
                        f"bundle {rel}: reference {reference} is a known gap: "
                        f"{KNOWN_UNRESOLVED_REFERENCES[relative]}"
                    )
                else:
                    report.error(f"bundle {rel}: unresolved reference {reference}")
    return checked


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repository root")
    parser.add_argument("--bundle", default=None, help="built schema bundle directory")
    args = parser.parse_args(argv)

    root = find_root(args.root)
    bundle = None
    if args.bundle:
        bundle = Path(args.bundle)
        if not bundle.is_absolute():
            bundle = (root / bundle).resolve()

    report = Report()
    files = markdown_files(root)
    workflows = workflow_files(root)
    check_encoding(root, files + workflows, report)
    check_markdown(root, files, report)
    check_mermaid(root, files, report)
    statuses = check_requirements(root, files, report)
    decisions = check_decisions(root, report)
    urls = check_schema_references(root, files, report)
    schemas = check_schema_files(root, bundle, report)
    workflow_count = check_workflows(root, workflows, report)

    print(f"files checked: {len(files)}")
    print(f"requirements: {len(statuses)} {dict(sorted(Counter(statuses.values()).items()))}")
    print(f"decisions: {decisions}")
    print(f"raw URLs: {urls}")
    print(f"schema files: {schemas}")
    print(f"workflows checked: {workflow_count}")
    print(f"errors: {len(report.errors)}")
    for error in report.errors:
        print(f"ERROR {error}")
    print(f"warnings: {len(report.warnings)}")
    for warning in report.warnings:
        print(f"WARN {warning}")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
