"""The number domain and the canonical number format of the document IR.

The numbers of the IR live in the binary64 number domain of ECMAScript, and
the canonical text of a number follows the `Number::toString` function of
ECMAScript. The TypeScript SDK uses the same domain and the same format, so
that both SDKs write and show the same text for the same number.
"""

from __future__ import annotations

import math
from decimal import Decimal

from typcast.diagnostics import CODE_NOT_SERIALIZABLE, raise_serialization

__all__ = [
    "format_number",
    "to_binary64",
]

# The largest integer that the binary64 domain holds exactly.
_MAX_EXACT_INTEGER = 2**53


def to_binary64(value: int) -> float:
    """Returns an integer in the number domain of the document IR.

    The canonical JSON text of the IR follows the number format of
    ECMAScript, so the numbers of a document live in the binary64 domain.
    An integer that the domain cannot hold exactly is rounded to the nearest
    representable value, exactly as TypeScript and `JSON.parse` do, and an
    integer that overflows the domain becomes an infinity.
    """
    try:
        return float(value)
    except OverflowError:
        # The conversion of an integer that the binary64 domain cannot hold
        # raises an error of the interpreter, while the domain holds an
        # infinity that keeps the sign of the integer, exactly as the
        # conversion of a number of ECMAScript does.
        return -math.inf if value < 0 else math.inf


def format_number(value: int | float) -> str:
    """Returns the canonical text of a number.

    The text follows the `Number::toString` function of ECMAScript: an
    integer-valued number holds no decimal point, a fraction holds the
    shortest text that reads back as the same number, and a number whose
    exponent lies outside the range of the plain form is written in the
    exponential form.
    """
    if isinstance(value, int) and not isinstance(value, bool):
        if -_MAX_EXACT_INTEGER <= value <= _MAX_EXACT_INTEGER:
            return str(value)
        return _format_float(to_binary64(value))
    return _format_float(value)


def _format_float(value: float) -> str:
    """Formats a number the way the JavaScript serializer formats it."""
    if math.isnan(value) or math.isinf(value):
        raise_serialization(
            CODE_NOT_SERIALIZABLE,
            "NaN and Infinity cannot be serialized.",
        )
    if value == 0:
        return "0"
    sign, digits, exponent = Decimal(repr(value)).as_tuple()
    coefficient = list(digits)
    while len(coefficient) > 1 and coefficient[-1] == 0:
        coefficient.pop()
        exponent += 1
    text = "".join(str(digit) for digit in coefficient)
    count = len(text)
    point = exponent + count
    if -6 < point <= 21:
        if point <= 0:
            body = "0." + "0" * (-point) + text
        elif point >= count:
            body = text + "0" * (point - count)
        else:
            body = text[:point] + "." + text[point:]
    else:
        mantissa = text[0] if count == 1 else text[0] + "." + text[1:]
        power = point - 1
        body = mantissa + "e" + ("+" if power >= 0 else "-") + str(abs(power))
    return ("-" if sign else "") + body
