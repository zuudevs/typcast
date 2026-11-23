import json
from pathlib import Path
from typing import Any

from typcast_codegen.errors import CodegenError


def parse_json_document(content: str, source: Path) -> Any:
    """Parse generated JSON and report syntax errors with source location."""
    try:
        return json.loads(content)
    except json.JSONDecodeError as error:
        raise CodegenError(
            f"{source}: invalid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
