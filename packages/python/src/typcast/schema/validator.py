"""The validation of an instance of the document IR against the JSON Schema contract.

The module holds a validator for the subset of JSON Schema 2020-12 that the
schema contract of the document IR uses. The contract itself is embedded in
the SDK as a generated source file, so an instance is checked against the
same documents that the release publishes, and the SDK needs no file of the
repository at run time.

The validator is a layer of its own. The reader keeps its own error contract,
and the semantic engine keeps the rules that JSON Schema cannot express. ADR
0027 records the decision.

The TypeScript SDK applies the same rules in `src/schema/validator.ts`, so
that both SDKs report the same diagnostics for the same instance.
"""

from __future__ import annotations

import posixpath
import re
from typing import Any, Mapping, Sequence

from typcast.diagnostics import (
    CODE_SCHEMA_UNSUPPORTED_KEYWORD,
    CODE_SCHEMA_VIOLATION,
    Diagnostic,
    safe_text,
    safe_value,
    validation_diagnostic,
)
from typcast.schema.schemas_generated import SCHEMAS

__all__ = [
    "ANNOTATION_KEYWORDS",
    "ASSERTION_KEYWORDS",
    "SCHEMA_ROOT",
    "schema_keywords",
    "validate_schema",
]

# The schema of the document IR. The bundle names it at the root.
SCHEMA_ROOT = "validator.schema.json"

# The keywords that carry no assertion. A schema may hold them, and the
# validator ignores them.
ANNOTATION_KEYWORDS = frozenset(
    {
        "$comment",
        "$defs",
        "$id",
        "$schema",
        "default",
        "deprecated",
        "description",
        "examples",
        "readOnly",
        "title",
        "writeOnly",
    }
)

# The keywords that the validator implements. Every other keyword is a
# violation of its own, so the validator never passes an instance that a rule
# of the schema would reject.
ASSERTION_KEYWORDS = frozenset(
    {
        "$ref",
        "additionalProperties",
        "const",
        "enum",
        "exclusiveMinimum",
        "items",
        "maxLength",
        "maximum",
        "minItems",
        "minLength",
        "minimum",
        "not",
        "oneOf",
        "pattern",
        "properties",
        "required",
        "type",
        "unevaluatedProperties",
    }
)

# The number of the allowed values that a message lists. A catalog holds more
# values than that, and a message that lists all of them is unreadable, so
# the message names the number of the values and the details hold the list.
MAXIMUM_LISTED_VALUES = 8


def validate_schema(value: Any) -> tuple[Diagnostic, ...]:
    """Returns the diagnostics of the schema contract for the value.

    The value is a JSON value. The function reports every rule that the value
    breaks and raises no error, so that a caller can show all of the problems
    at once.
    """
    unsupported = _unsupported_keywords(SCHEMAS)
    if unsupported:
        return tuple(
            _unsupported_violation(document, keyword)
            for document, keyword in unsupported
        )
    evaluator = _Evaluator(SCHEMAS)
    diagnostics, _ = evaluator.evaluate(value, SCHEMAS[SCHEMA_ROOT], "", SCHEMA_ROOT)
    return tuple(diagnostics)


def schema_keywords() -> tuple[str, ...]:
    """Returns the keywords that the schema contract uses.

    The function walks every schema document of the contract, so a keyword
    that the validator does not implement is visible before a document is
    validated.
    """
    found: set[str] = set()
    for document in SCHEMAS.values():
        _walk(document, found)
    return tuple(sorted(found))


def _unsupported_keywords(
    documents: Mapping[str, Any],
) -> list[tuple[str, str]]:
    """Returns the keywords that the validator does not implement.

    The result names the document that holds the keyword and the keyword
    itself, so that a caller can find the place that needs a new rule.
    """
    unsupported: list[tuple[str, str]] = []
    for path in sorted(documents):
        found: set[str] = set()
        _walk(documents[path], found)
        for keyword in sorted(found):
            if keyword in ANNOTATION_KEYWORDS or keyword in ASSERTION_KEYWORDS:
                continue
            unsupported.append((path, keyword))
    return unsupported


def _walk(schema: Any, found: set[str]) -> None:
    """Collects the keywords of a schema document and of its subschemas."""
    if not isinstance(schema, dict):
        return
    for keyword, value in schema.items():
        found.add(keyword)
        if keyword in ("properties", "$defs") and isinstance(value, dict):
            for subschema in value.values():
                _walk(subschema, found)
        elif keyword in (
            "items",
            "additionalProperties",
            "unevaluatedProperties",
            "not",
        ) and isinstance(value, dict):
            _walk(value, found)
        elif keyword in ("oneOf", "anyOf", "allOf") and isinstance(value, list):
            for subschema in value:
                _walk(subschema, found)


class _Evaluator:
    """Applies the keywords of a schema to an instance."""

    def __init__(self, schemas: Mapping[str, Any]) -> None:
        self._schemas = schemas

    def evaluate(
        self,
        value: Any,
        schema: Any,
        path: str,
        base: str,
    ) -> tuple[list[Diagnostic], set[str]]:
        """Returns the diagnostics of the value and the properties it evaluates.

        The properties are the names that the schema evaluates, and the
        keyword `unevaluatedProperties` needs them.
        """
        diagnostics: list[Diagnostic] = []
        evaluated: set[str] = set()
        if not isinstance(schema, dict):
            raise _SchemaError(f"the schema of '{_location(path)}' is not an object")

        if "$ref" in schema:
            target, target_base = self._resolve(schema["$ref"], base)
            sub_diagnostics, sub_evaluated = self.evaluate(
                value, target, path, target_base
            )
            diagnostics.extend(sub_diagnostics)
            evaluated |= sub_evaluated

        if "type" in schema and not _matches_type(value, schema["type"]):
            diagnostics.append(_type_violation(path, schema["type"], value))

        if "const" in schema and not _equal(value, schema["const"]):
            diagnostics.append(_const_violation(path, schema["const"], value))

        if "enum" in schema and not any(
            _equal(value, allowed) for allowed in schema["enum"]
        ):
            diagnostics.append(_enum_violation(path, schema["enum"], value))

        if isinstance(value, dict):
            diagnostics.extend(self._evaluate_object(value, schema, path, base, evaluated))

        if isinstance(value, list):
            diagnostics.extend(self._evaluate_array(value, schema, path, base))

        if isinstance(value, str):
            diagnostics.extend(self._evaluate_text(value, schema, path))

        if _is_number(value):
            diagnostics.extend(self._evaluate_number(value, schema, path))

        if "not" in schema:
            sub_diagnostics, _ = self.evaluate(value, schema["not"], path, base)
            if not sub_diagnostics:
                diagnostics.append(_not_violation(path))

        union_diagnostics, union_evaluated = self._evaluate_union(
            value, schema, path, base
        )
        diagnostics.extend(union_diagnostics)
        evaluated |= union_evaluated

        if isinstance(value, dict) and "unevaluatedProperties" in schema:
            diagnostics.extend(
                self._evaluate_unevaluated(value, schema, path, base, evaluated)
            )

        return diagnostics, evaluated

    def _evaluate_object(
        self,
        value: Mapping[str, Any],
        schema: Mapping[str, Any],
        path: str,
        base: str,
        evaluated: set[str],
    ) -> list[Diagnostic]:
        """Applies the object keywords of the schema.

        The set of the evaluated properties holds the properties that the
        keywords of the schema and the schemas that it references evaluate,
        because the keyword `unevaluatedProperties` rejects every property
        that none of them evaluates.
        """
        diagnostics: list[Diagnostic] = []
        properties = schema.get("properties", {})
        if not isinstance(properties, dict):
            raise _SchemaError(
                f"the properties of '{_location(path)}' are not an object"
            )

        for name, subschema in properties.items():
            if name in value:
                sub_diagnostics, _ = self.evaluate(
                    value[name], subschema, f"{path}/{_escape(name)}", base
                )
                diagnostics.extend(sub_diagnostics)
                evaluated.add(name)

        required = schema.get("required", [])
        if not isinstance(required, list):
            raise _SchemaError(
                f"the required list of '{_location(path)}' is not an array"
            )
        for name in required:
            if name not in value:
                diagnostics.append(_required_violation(path, name))

        if "additionalProperties" in schema:
            extra = schema["additionalProperties"]
            for name in sorted(value):
                if name in properties:
                    continue
                if extra is False:
                    diagnostics.append(_unknown_violation(path, name))
                else:
                    sub_diagnostics, _ = self.evaluate(
                        value[name], extra, f"{path}/{_escape(name)}", base
                    )
                    diagnostics.extend(sub_diagnostics)
                evaluated.add(name)

        return diagnostics

    def _evaluate_unevaluated(
        self,
        value: Mapping[str, Any],
        schema: Mapping[str, Any],
        path: str,
        base: str,
        evaluated: set[str],
    ) -> list[Diagnostic]:
        """Applies the keyword `unevaluatedProperties` of the schema.

        The keyword rejects every property that no keyword of the schema and
        no schema that it references evaluates. The check runs after every
        other keyword, because the union keywords evaluate properties too.
        """
        diagnostics: list[Diagnostic] = []
        extra = schema["unevaluatedProperties"]
        for name in sorted(value):
            if name in evaluated:
                continue
            if extra is False:
                diagnostics.append(_unevaluated_violation(path, name))
            else:
                sub_diagnostics, _ = self.evaluate(
                    value[name], extra, f"{path}/{_escape(name)}", base
                )
                diagnostics.extend(sub_diagnostics)
            evaluated.add(name)
        return diagnostics

    def _evaluate_array(
        self,
        value: list[Any],
        schema: Mapping[str, Any],
        path: str,
        base: str,
    ) -> list[Diagnostic]:
        """Applies the array keywords of the schema."""
        diagnostics: list[Diagnostic] = []
        if "minItems" in schema and len(value) < schema["minItems"]:
            diagnostics.append(_min_items_violation(path, schema["minItems"]))
        if "items" in schema:
            for index, item in enumerate(value):
                sub_diagnostics, _ = self.evaluate(
                    item, schema["items"], f"{path}/{index}", base
                )
                diagnostics.extend(sub_diagnostics)
        return diagnostics

    def _evaluate_text(
        self,
        value: str,
        schema: Mapping[str, Any],
        path: str,
    ) -> list[Diagnostic]:
        """Applies the string keywords of the schema."""
        diagnostics: list[Diagnostic] = []
        if "minLength" in schema and len(value) < schema["minLength"]:
            diagnostics.append(_min_length_violation(path, schema["minLength"]))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            diagnostics.append(_max_length_violation(path, schema["maxLength"]))
        if "pattern" in schema and not _matches_pattern(schema["pattern"], value):
            diagnostics.append(_pattern_violation(path, schema["pattern"]))
        return diagnostics

    def _evaluate_number(
        self,
        value: float,
        schema: Mapping[str, Any],
        path: str,
    ) -> list[Diagnostic]:
        """Applies the number keywords of the schema."""
        diagnostics: list[Diagnostic] = []
        if "minimum" in schema and value < schema["minimum"]:
            diagnostics.append(_minimum_violation(path, schema["minimum"], value))
        if "maximum" in schema and value > schema["maximum"]:
            diagnostics.append(_maximum_violation(path, schema["maximum"], value))
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            diagnostics.append(
                _exclusive_minimum_violation(path, schema["exclusiveMinimum"], value)
            )
        return diagnostics

    def _evaluate_union(
        self,
        value: Any,
        schema: Mapping[str, Any],
        path: str,
        base: str,
    ) -> tuple[list[Diagnostic], set[str]]:
        """Applies the union keyword of the schema.

        The union of the contract uses a `type` discriminator with a `const`
        value in every branch. When the value names a discriminator that one
        branch declares, the violations of that branch are the useful ones,
        so they are reported instead of the violation of the union.
        """
        diagnostics: list[Diagnostic] = []
        evaluated: set[str] = set()
        if "oneOf" not in schema:
            return diagnostics, evaluated
        branches = schema["oneOf"]
        if not isinstance(branches, list):
            raise _SchemaError(
                f"the branches of '{_location(path)}' are not an array"
            )
        results: list[tuple[list[Diagnostic], set[str]]] = []
        matched = 0
        for branch in branches:
            sub_diagnostics, sub_evaluated = self.evaluate(value, branch, path, base)
            results.append((sub_diagnostics, sub_evaluated))
            if not sub_diagnostics:
                matched += 1
        if matched == 1:
            for sub_diagnostics, sub_evaluated in results:
                if not sub_diagnostics:
                    evaluated |= sub_evaluated
            return diagnostics, evaluated
        index = _matching_branch(value, branches)
        if index is not None:
            diagnostics.extend(results[index][0])
            evaluated |= results[index][1]
            return diagnostics, evaluated
        diagnostics.append(_union_violation(path, matched, branches))
        return diagnostics, evaluated

    def _resolve(self, reference: Any, base: str) -> tuple[Any, str]:
        """Resolves a reference against the document that holds it.

        A reference that starts with `#` names a location inside the document
        itself. Every other reference names a file of the bundle, relative to
        the directory of the document that holds it, and it may carry a
        pointer to a location inside that file.
        """
        if not isinstance(reference, str) or not reference:
            raise _SchemaError(f"the reference of '{base}' must be a non-empty text")
        file_part, _, pointer = reference.partition("#")
        if not file_part:
            target = self._schemas.get(base)
            target_base = base
        else:
            target_base = posixpath.normpath(
                posixpath.join(posixpath.dirname(base), file_part)
            )
            target = self._schemas.get(target_base)
        if target is None:
            raise _SchemaError(
                f"the bundle holds no schema document at '{target_base}'"
            )
        if pointer:
            target = _resolve_pointer(target, pointer, reference)
        return target, target_base


class _SchemaError(Exception):
    """Raised when the schema contract itself is malformed."""


# ---------------------------------------------------------------------------
# The JSON value helpers
# ---------------------------------------------------------------------------


def _is_number(value: Any) -> bool:
    """Returns whether the value is a JSON number."""
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _matches_type(value: Any, expected: Any) -> bool:
    """Returns whether the value matches the type of the schema."""
    names = expected if isinstance(expected, list) else [expected]
    for name in names:
        if name == "object" and isinstance(value, dict):
            return True
        if name == "array" and isinstance(value, list):
            return True
        if name == "string" and isinstance(value, str):
            return True
        if name == "boolean" and isinstance(value, bool):
            return True
        if name == "null" and value is None:
            return True
        if name == "number" and _is_number(value):
            return True
        if name == "integer" and _is_number(value) and float(value).is_integer():
            return True
    return False


def _equal(left: Any, right: Any) -> bool:
    """Returns whether two JSON values are equal."""
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if _is_number(left) and _is_number(right):
        return float(left) == float(right)
    if isinstance(left, str) and isinstance(right, str):
        return left == right
    if left is None or right is None:
        return left is None and right is None
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(
            _equal(one, other) for one, other in zip(left, right)
        )
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(
            _equal(left[name], right[name]) for name in left
        )
    return False


def _escape(token: str) -> str:
    """Escapes a token of a JSON Pointer as RFC 6901 defines it."""
    return token.replace("~", "~0").replace("/", "~1")


def _location(path: str) -> str:
    """Returns the path of a location as a diagnostic names it."""
    return path or "/"


def _matching_branch(value: Any, branches: Sequence[Any]) -> int | None:
    """Returns the branch whose discriminator matches the value.

    The union of the contract names a `type` discriminator with a `const`
    value in every branch. The branch whose discriminator matches the value
    is the one that describes the value, so its violations are the useful
    ones.
    """
    if not isinstance(value, dict):
        return None
    discriminator = value.get("type")
    if not isinstance(discriminator, str):
        return None
    matches: list[int] = []
    for index, branch in enumerate(branches):
        if not isinstance(branch, dict):
            continue
        properties = branch.get("properties")
        if not isinstance(properties, dict):
            continue
        type_schema = properties.get("type")
        if not isinstance(type_schema, dict):
            continue
        if type_schema.get("const") == discriminator:
            matches.append(index)
    if len(matches) == 1:
        return matches[0]
    return None


def _discriminators(branches: Sequence[Any]) -> list[str]:
    """Returns the discriminator values of the branches of a union."""
    values: list[str] = []
    for branch in branches:
        if not isinstance(branch, dict):
            continue
        properties = branch.get("properties")
        if not isinstance(properties, dict):
            continue
        type_schema = properties.get("type")
        if not isinstance(type_schema, dict):
            continue
        constant = type_schema.get("const")
        if isinstance(constant, str):
            values.append(constant)
    return values


def _resolve_pointer(document: Any, pointer: str, reference: str) -> Any:
    """Returns the value that a JSON Pointer names in a document."""
    if not pointer.startswith("/"):
        raise _SchemaError(
            f"the reference '{reference}' carries a pointer that is not a JSON Pointer"
        )
    value = document
    for token in pointer.split("/")[1:]:
        name = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict):
            if name not in value:
                raise _SchemaError(
                    f"the reference '{reference}' names no value of the document"
                )
            value = value[name]
        elif isinstance(value, list):
            try:
                index = int(name)
            except ValueError:
                raise _SchemaError(
                    f"the reference '{reference}' names no value of the document"
                ) from None
            if index < 0 or index >= len(value):
                raise _SchemaError(
                    f"the reference '{reference}' names no value of the document"
                )
            value = value[index]
        else:
            raise _SchemaError(
                f"the reference '{reference}' names no value of the document"
            )
    return value


# ---------------------------------------------------------------------------
# The patterns of the schema
# ---------------------------------------------------------------------------


def _matches_pattern(pattern: str, value: str) -> bool:
    """Returns whether the text matches the pattern of the schema.

    The pattern of a schema is a pattern of ECMAScript, and it matches
    anywhere in the text. The engine of Python differs from the engine of
    ECMAScript in the meaning of the anchor `$` and in the meaning of the
    character classes such as `\\d`, so the pattern is translated before it
    is compiled.
    """
    try:
        compiled = re.compile(_translate_pattern(pattern), re.ASCII)
    except re.error as error:
        raise _SchemaError(
            f"the pattern '{pattern}' is not a valid regular expression: {error}"
        ) from None
    return compiled.search(value) is not None


def _translate_pattern(pattern: str) -> str:
    """Translates the anchor `$` of a pattern for the engine of Python.

    The `$` of ECMAScript matches the end of the text only, while the `$` of
    Python also matches before a newline at the end of the text. The
    translation replaces every `$` that is not escaped and that is not part
    of a character class with the end anchor of Python.
    """
    result: list[str] = []
    in_class = False
    index = 0
    length = len(pattern)
    while index < length:
        char = pattern[index]
        if char == "\\":
            result.append(pattern[index : index + 2])
            index += 2
            continue
        if in_class:
            result.append(char)
            if char == "]":
                in_class = False
            index += 1
            continue
        if char == "[":
            in_class = True
            result.append(char)
            index += 1
            continue
        if char == "$":
            result.append(r"\Z")
            index += 1
            continue
        result.append(char)
        index += 1
    return "".join(result)


# ---------------------------------------------------------------------------
# The violations
# ---------------------------------------------------------------------------


def _type_violation(path: str, expected: Any, value: Any) -> Diagnostic:
    names = expected if isinstance(expected, list) else [expected]
    name = ", ".join(str(item) for item in names)
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must be a JSON {name}.",
        path or None,
        {"keyword": "type", "expected": name, "value": safe_value(value)},
    )


def _const_violation(path: str, expected: Any, value: Any) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must be '{safe_text(expected)}'.",
        path or None,
        {
            "keyword": "const",
            "expected": safe_value(expected),
            "value": safe_value(value),
        },
    )


def _enum_violation(path: str, allowed: Any, value: Any) -> Diagnostic:
    names = [str(item) for item in allowed]
    if len(names) > MAXIMUM_LISTED_VALUES:
        message = (
            f"'{_location(path)}' must be one of the {len(names)} allowed values, "
            f"got '{safe_text(value)}'."
        )
    else:
        message = (
            f"'{_location(path)}' must be one of {', '.join(names)}, "
            f"got '{safe_text(value)}'."
        )
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        message,
        path or None,
        {"keyword": "enum", "allowed": list(allowed), "value": safe_value(value)},
    )


def _required_violation(path: str, name: str) -> Diagnostic:
    location = f"{path}/{_escape(name)}"
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{location}' is required.",
        location,
        {"keyword": "required", "field": name},
    )


def _unknown_violation(path: str, name: str) -> Diagnostic:
    location = f"{path}/{_escape(name)}"
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{location}' is not a known field.",
        location,
        {"keyword": "additionalProperties", "field": name},
    )


def _unevaluated_violation(path: str, name: str) -> Diagnostic:
    location = f"{path}/{_escape(name)}"
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{location}' is not a known field.",
        location,
        {"keyword": "unevaluatedProperties", "field": name},
    )


def _min_items_violation(path: str, limit: int) -> Diagnostic:
    if limit == 1:
        message = f"'{_location(path)}' must not be empty."
    else:
        message = f"'{_location(path)}' must hold at least {limit} items."
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        message,
        path or None,
        {"keyword": "minItems", "minItems": limit},
    )


def _min_length_violation(path: str, limit: int) -> Diagnostic:
    if limit == 1:
        message = f"'{_location(path)}' must not be empty."
    else:
        message = f"'{_location(path)}' must hold at least {limit} code points."
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        message,
        path or None,
        {"keyword": "minLength", "minLength": limit},
    )


def _max_length_violation(path: str, limit: int) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must not hold more than {limit} code points.",
        path or None,
        {"keyword": "maxLength", "maxLength": limit},
    )


def _pattern_violation(path: str, pattern: str) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must match the pattern {pattern}.",
        path or None,
        {"keyword": "pattern", "pattern": pattern},
    )


def _minimum_violation(path: str, limit: float, value: float) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must not be less than {limit}.",
        path or None,
        {"keyword": "minimum", "minimum": limit, "value": safe_value(value)},
    )


def _maximum_violation(path: str, limit: float, value: float) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must not be greater than {limit}.",
        path or None,
        {"keyword": "maximum", "maximum": limit, "value": safe_value(value)},
    )


def _exclusive_minimum_violation(path: str, limit: float, value: float) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must be greater than {limit}.",
        path or None,
        {
            "keyword": "exclusiveMinimum",
            "exclusiveMinimum": limit,
            "value": safe_value(value),
        },
    )


def _not_violation(path: str) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        f"'{_location(path)}' must not match the schema.",
        path or None,
        {"keyword": "not"},
    )


def _union_violation(
    path: str,
    matched: int,
    branches: Sequence[Any],
) -> Diagnostic:
    if matched == 0:
        message = (
            f"'{_location(path)}' must match one alternative of the schema, "
            "but matches none."
        )
    else:
        message = (
            f"'{_location(path)}' must match one alternative of the schema, "
            f"but matches {matched}."
        )
    details: dict[str, Any] = {"keyword": "oneOf", "matched": matched}
    allowed = _discriminators(branches)
    if allowed:
        details["allowed"] = allowed
    return validation_diagnostic(
        CODE_SCHEMA_VIOLATION,
        message,
        path or None,
        details,
    )


def _unsupported_violation(document: str, keyword: str) -> Diagnostic:
    return validation_diagnostic(
        CODE_SCHEMA_UNSUPPORTED_KEYWORD,
        (
            f"The schema '{document}' uses the keyword '{keyword}', which the "
            "validator does not implement."
        ),
        None,
        {"keyword": keyword, "schema": document},
    )
