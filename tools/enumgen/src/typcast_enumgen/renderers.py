"""The renderers of the generated source files of the SDKs.

A generated file names the catalog it comes from and states that it must not
be edited, so that a hand-written change to a generated file is visible in
the review of the change. The output is deterministic: the same catalog
always renders the same text, on every platform.
"""

from __future__ import annotations

import json

from typcast_enumgen.errors import EnumgenError

__all__ = ["render_python", "render_typescript"]

# The languages that the generator can write.
LANGUAGES = ("typescript", "python")

_NOTE = (
    "This file is generated. Do not edit it; change the catalog and rebuild."
)


def _literal(value: str) -> str:
    """Returns a source literal of a value of the catalog.

    The literal is the JSON form of the value, and both languages accept it,
    so a value that holds a quote, a backslash, or a control character never
    breaks the generated file.
    """
    return json.dumps(value, ensure_ascii=False)


def _check_name(constant_name: str) -> None:
    """Checks that the name of the constant is an upper-case identifier."""
    if not constant_name:
        raise EnumgenError("the name of the constant must not be empty.")
    if not constant_name.replace("_", "").isalnum():
        raise EnumgenError(
            f"the name of the constant must be an identifier, got "
            f"{constant_name!r}."
        )
    if constant_name != constant_name.upper():
        raise EnumgenError(
            f"the name of the constant must be upper case, got "
            f"{constant_name!r}."
        )


def render_typescript(
    values: list[str],
    constant_name: str,
    catalog_label: str,
) -> str:
    """Returns the TypeScript source of a constant that holds the values."""
    _check_name(constant_name)
    lines = [
        "/**",
        f" * The values of the catalog `{catalog_label}`.",
        " *",
        f" * {_NOTE}",
        " */",
        "",
        f"export const {constant_name}: readonly string[] = [",
    ]
    for value in values:
        lines.append(f"  {_literal(value)},")
    lines.append("];")
    lines.append("")
    return "\n".join(lines)


def render_python(
    values: list[str],
    constant_name: str,
    catalog_label: str,
) -> str:
    """Returns the Python source of a constant that holds the values."""
    _check_name(constant_name)
    lines = [
        f'"""The values of the catalog `{catalog_label}`.',
        "",
        _NOTE,
        '"""',
        "",
        f"{constant_name}: tuple[str, ...] = (",
    ]
    for value in values:
        lines.append(f"    {_literal(value)},")
    lines.append(")")
    lines.append("")
    return "\n".join(lines)
