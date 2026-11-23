import json
import re
from pathlib import Path

from typcast_codegen.errors import CodegenError
from typcast_codegen.readers.csv_reader import read_csv_column


PLACEHOLDER_PATTERN = re.compile(
    r"<(?P<path>[^<>:\r\n]+):(?P<column>[^<>:\r\n]+)>"
)


def replace_placeholders(template_text: str, template_path: Path) -> str:
    """Replace CSV-column placeholders in a template.

    Paths in placeholders are resolved relative to the template's directory.
    Values are encoded as JSON arrays so they can be inserted into JSON text.
    """
    template_directory = template_path.resolve().parent
    cache: dict[tuple[Path, str], list[str]] = {}

    def replace(match: re.Match[str]) -> str:
        raw_path = match.group("path").strip()
        column_name = match.group("column").strip()

        if not raw_path:
            raise CodegenError("Placeholder source path cannot be empty.")

        if not column_name:
            raise CodegenError("Placeholder column name cannot be empty.")

        source_reference = Path(raw_path)

        if source_reference.is_absolute():
            raise CodegenError(
                f"Placeholder path must be relative to the template: {raw_path!r}."
            )

        csv_path = (template_directory / source_reference).resolve()
        cache_key = (csv_path, column_name)

        if cache_key not in cache:
            cache[cache_key] = read_csv_column(csv_path, column_name)

        return json.dumps(cache[cache_key], ensure_ascii=False)

    return PLACEHOLDER_PATTERN.sub(replace, template_text)
