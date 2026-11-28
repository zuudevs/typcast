"""The Typst emitter of the document IR.

The module holds the emitter of the Python SDK. The TypeScript SDK applies the
same rules in `src/emitter/emitter.ts`, so that both SDKs produce the same
bytes for the same document.
"""

from typcast.emitter.emitter import (
    EMITTER_HEADER,
    emit_typst,
    escape_string,
    escape_text,
    format_length,
    normalize_path,
)

__all__ = [
    "EMITTER_HEADER",
    "emit_typst",
    "escape_string",
    "escape_text",
    "format_length",
    "normalize_path",
]
