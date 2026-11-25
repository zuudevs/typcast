import json
from typing import Any


def render_json_document(value: Any) -> str:
    """Render a Python JSON value as readable UTF-8 JSON."""
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
    ) + "\n"
