"""Contract checks for the built schema bundle.

The bundle that `//specs/schemas:schema_bundle` produces is the authoritative
artifact set (ADR-0023). This target validates that bundle against the rules
in `docs/specifications/schema.md`:

- Every file is UTF-8 JSON without a byte order mark.
- Every file declares the draft 2020-12 dialect.
- Every file declares an absolute, unique `$id` that matches its published
  versioned raw URL.
- Every relative `$ref` resolves inside the bundle.
- Every object schema is closed and declares its required list.
- Every union uses a `type` discriminator with `const` values.

The prototype bundle does not satisfy the rules yet. Every violation is
therefore compared with the open prototype defects in the schema contract. A
violation that no open defect explains fails the target, and a tracked
violation that no longer occurs fails the target too, so the defect list
shrinks as the schema migration proceeds.

Usage:

    bazel test //specs/schemas:schema_tests
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

DIALECT = "https://json-schema.org/draft/2020-12/schema"
PUBLISHED_BASE = "https://raw.githubusercontent.com/zuudevs/typcast/"
PUBLISHED_PATTERN = re.compile(
    r"^https://raw\.githubusercontent\.com/zuudevs/typcast/"
    r"(?P<tag>[^/]+)/specs/schemas/(?P<path>.+)$"
)
RELEASE_TAG_PATTERN = re.compile(r"^v\d+\.\d+\.\d+")

# Violations that an open prototype defect explains. The key is
# "<rule>:<file>[:<location>]" and the value is the defect that tracks it.
KNOWN_VIOLATIONS = {
    "dialect:api/types/length.schema.json": "SCH-D05",
    "dialect:api/types/paper.schema.json": "SCH-D05",
    "identity:api/types/length.schema.json": "SCH-D05",
    "identity:api/types/paper.schema.json": "SCH-D05",
    "identity-base:api/types/alignment.schema.json": "SCH-D10",
    "identity-base:definitions/bound.schema.json": "SCH-D10",
    "identity-base:validator.schema.json": "SCH-D10",
    "identity-path:api/types/alignment.schema.json": "SCH-D03",
    "identity-path:validator.schema.json": "SCH-D04",
    "reference:validator.schema.json:./definitions/node.schema.json": "SCH-D01",
    "closed:api/types/length.schema.json:/": "SCH-D06",
    "closed:api/types/paper.schema.json:/": "SCH-D06",
    "closed:api/types/paper.schema.json:properties/paper": "SCH-D06",
    "closed:definitions/bound.schema.json:/": "SCH-D06",
    "closed:validator.schema.json:/": "SCH-D06",
    "closed:validator.schema.json:properties/contents/items": "SCH-D06",
    "closed:validator.schema.json:properties/modules": "SCH-D06",
    "closed:validator.schema.json:properties/page": "SCH-D06",
    "closed:validator.schema.json:properties/page/properties/paper": "SCH-D06",
    "required-missing:api/types/length.schema.json:/": "SCH-D06",
    "required-missing:api/types/paper.schema.json:/": "SCH-D06",
    "required-missing:api/types/paper.schema.json:properties/paper": "SCH-D06",
    "required-missing:definitions/bound.schema.json:/": "SCH-D06",
    "required-missing:validator.schema.json:properties/contents/items": "SCH-D06",
    "required-missing:validator.schema.json:properties/page": "SCH-D06",
    "required-missing:validator.schema.json:properties/page/properties/paper": "SCH-D06",
}


def find_bundle_root() -> Path:
    """Locates the built bundle in a Bazel runfiles tree or in a checkout."""
    candidates: list[Path] = []
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
    here = Path(__file__).resolve()
    candidates.extend(here.parents)
    for candidate in candidates:
        bundle = candidate / "specs" / "schemas"
        generated = bundle / "api" / "types"
        if not (bundle / "validator.schema.json").exists():
            continue
        # The source tree holds only the static schemas. The built bundle also
        # holds the generated ones, so the test never validates the source.
        if generated.is_dir() and any(generated.glob("*.json")):
            return bundle
    raise SystemExit("schema bundle not found; run the target through Bazel")


def object_schemas(document: object, location: str = "") -> list[tuple[str, dict]]:
    """Returns the object schemas of a document with their locations."""
    found: list[tuple[str, dict]] = []
    if isinstance(document, dict):
        if document.get("type") == "object" or "properties" in document:
            found.append((location, document))
        for key, value in document.items():
            if key == "properties":
                for name, subschema in value.items():
                    if isinstance(subschema, dict):
                        found.extend(object_schemas(subschema, f"{location}/properties/{name}"))
            elif key in ("items", "additionalProperties", "unevaluatedProperties"):
                if isinstance(value, dict):
                    found.extend(object_schemas(value, f"{location}/{key}"))
            elif key in ("oneOf", "anyOf", "allOf", "prefixItems"):
                if isinstance(value, list):
                    for index, subschema in enumerate(value):
                        if isinstance(subschema, dict):
                            found.extend(object_schemas(subschema, f"{location}/{key}/{index}"))
            elif key not in ("$defs",):
                found.extend(object_schemas(value, f"{location}/{key}"))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            found.extend(object_schemas(value, f"{location}/{index}"))
    return found


def collect_references(document: object, location: str = "") -> list[tuple[str, str]]:
    """Returns the relative references of a document with their locations."""
    references: list[tuple[str, str]] = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "$ref" and isinstance(value, str):
                references.append((location or "/", value))
            else:
                references.extend(collect_references(value, f"{location}/{key}"))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            references.extend(collect_references(value, f"{location}/{index}"))
    return references


def collect_unions(document: object, location: str = "") -> list[tuple[str, dict]]:
    """Returns the unions of a document with their locations."""
    unions: list[tuple[str, dict]] = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key in ("oneOf", "anyOf") and isinstance(value, list):
                unions.append((f"{location}/{key}", document))
            unions.extend(collect_unions(value, f"{location}/{key}"))
    elif isinstance(document, list):
        for index, value in enumerate(document):
            unions.extend(collect_unions(value, f"{location}/{index}"))
    return unions


def check_file(path: Path, relative: str, bundle: Path) -> tuple[list[str], list[str]]:
    """Returns the violation keys and the identifiers of one bundle file."""
    violations: list[str] = []
    identifiers: list[str] = []
    data = path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        violations.append(f"encoding:{relative}")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        violations.append(f"encoding:{relative}")
        return violations, identifiers
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        violations.append(f"syntax:{relative}")
        return violations, identifiers

    dialect = document.get("$schema") if isinstance(document, dict) else None
    if dialect != DIALECT:
        violations.append(f"dialect:{relative}")

    identifier = document.get("$id") if isinstance(document, dict) else None
    if not isinstance(identifier, str) or not identifier:
        violations.append(f"identity:{relative}")
    else:
        identifiers.append(identifier)
        if not identifier.startswith(PUBLISHED_BASE):
            violations.append(f"identity-base:{relative}")
        else:
            published = PUBLISHED_PATTERN.match(identifier)
            if published is None:
                violations.append(f"identity-format:{relative}")
            elif not RELEASE_TAG_PATTERN.match(published.group("tag")):
                violations.append(f"identity-tag:{relative}")
        expected = relative.split("/")
        actual = identifier.split("/")
        if actual[-len(expected):] != expected:
            violations.append(f"identity-path:{relative}")

    for _, reference in collect_references(document):
        if reference.startswith(("#", "http://", "https://")):
            continue
        target = (path.parent / reference).resolve()
        if not target.exists():
            violations.append(f"reference:{relative}:{reference}")

    for location, schema in object_schemas(document, "/"):
        if schema.get("additionalProperties") is not False and \
                schema.get("unevaluatedProperties") is not False:
            violations.append(f"closed:{relative}:{location.strip('/') or '/'}")
        required = schema.get("required")
        properties = schema.get("properties", {})
        if not isinstance(required, list):
            violations.append(f"required-missing:{relative}:{location.strip('/') or '/'}")
        elif isinstance(properties, dict):
            for name in required:
                if name not in properties:
                    violations.append(
                        f"required-unknown:{relative}:{location.strip('/') or '/'}:{name}"
                    )

    for location, schema in collect_unions(document):
        branches = schema.get(location.rsplit("/", 1)[-1], [])
        if not isinstance(branches, list):
            continue
        constants: list[object] = []
        for branch in branches:
            if not isinstance(branch, dict):
                continue
            properties = branch.get("properties", {})
            discriminator = properties.get("type", {}) if isinstance(properties, dict) else {}
            if not isinstance(discriminator, dict) or "const" not in discriminator:
                violations.append(f"discriminator:{relative}:{location}")
                break
            constants.append(discriminator["const"])
        else:
            if len(set(map(repr, constants))) != len(constants):
                violations.append(f"discriminator-duplicate:{relative}:{location}")

    return violations, identifiers


def main() -> int:
    bundle = find_bundle_root()
    files = sorted(path for path in bundle.rglob("*.json") if path.is_file())
    if not files:
        print("ERROR no schema files found in the bundle")
        return 1

    violations: list[str] = []
    identifiers: dict[str, list[str]] = {}
    for path in files:
        relative = path.relative_to(bundle).as_posix()
        file_violations, file_identifiers = check_file(path, relative, bundle)
        violations.extend(file_violations)
        for identifier in file_identifiers:
            identifiers.setdefault(identifier, []).append(relative)

    for identifier, owners in sorted(identifiers.items()):
        if len(owners) > 1:
            violations.append(f"identity-unique:{identifier}")

    violations.sort()
    untracked = [item for item in violations if item not in KNOWN_VIOLATIONS]
    stale = [item for item in KNOWN_VIOLATIONS if item not in violations]
    tracked = Counter(KNOWN_VIOLATIONS[item] for item in violations if item in KNOWN_VIOLATIONS)

    print(f"bundle files: {len(files)}")
    print(f"violations: {len(violations)}")
    for item in violations:
        marker = "KNOWN" if item in KNOWN_VIOLATIONS else "NEW"
        defect = KNOWN_VIOLATIONS.get(item, "")
        print(f"{marker} {item} {defect}".rstrip())
    print(f"known defects still present: {dict(sorted(tracked.items()))}")

    errors = 0
    for item in untracked:
        print(f"ERROR untracked violation: {item}")
        errors += 1
    for item in stale:
        print(f"ERROR stale known violation: {item}")
        errors += 1
    print(f"errors: {errors}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
