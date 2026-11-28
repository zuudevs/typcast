"""The checks of the arguments of the public API.

The type of an argument of a public method is a rule of the API and not a rule
of the document, so the SDK checks it itself. A value of an unexpected type
is reported with `TYPCAST-API-0001` and the phase `api`.

The module is shared by the builder and by the emitter, so that both report
the same diagnostic for the same value. The TypeScript SDK applies the same
rules in `src/api.ts`.
"""

from __future__ import annotations

from typing import Any, NoReturn, Sequence

from typcast.diagnostics import CODE_INVALID_ARGUMENT, raise_api

__all__ = [
    "reject_api_argument",
    "require_api_instance",
    "require_api_number",
    "require_api_sequence",
    "require_api_string",
]


def reject_api_argument(path: str, expected: str) -> NoReturn:
    """Raises a public API error for a value of an unexpected type."""
    raise_api(
        CODE_INVALID_ARGUMENT,
        f"'{path}' must be {expected}.",
        path,
        {"expected": expected},
    )


def require_api_string(value: Any, path: str) -> str:
    """Returns a string argument after checking its type."""
    if not isinstance(value, str):
        reject_api_argument(path, "a string")
    return value


def require_api_number(value: Any, path: str) -> float:
    """Returns a numeric argument after checking its type.

    A boolean is not a number of the IR, so it is rejected here.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        reject_api_argument(path, "a number")
    return value


def require_api_instance(
    value: Any,
    expected: type,
    path: str,
    name: str,
) -> Any:
    """Returns a model argument after checking its type."""
    if not isinstance(value, expected):
        reject_api_argument(path, f"a {name}")
    return value


def require_api_sequence(value: Any, path: str, expected: str) -> Sequence[Any]:
    """Returns a sequence argument after checking its type.

    A string is a sequence of characters and not a sequence of elements, so it
    is rejected here, exactly as the model rejects it.
    """
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        reject_api_argument(path, expected)
    return value
