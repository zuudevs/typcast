from pathlib import Path
from typing import Sequence

from typcast_codegen.errors import CodegenError
from typcast_codegen.parsers.placeholder import replace_placeholders
from typcast_codegen.renderers.json_renderer import render_json_document
from typcast_codegen.validators.json_validator import parse_json_document


def generate_json_text(
    input_path: Path,
    catalogs: Sequence[Path] | None = None,
) -> str:
    """Generate and validate JSON from a template file.

    The catalogs are the inputs that the build declares for the template.
    When they are given, every placeholder must resolve to one of them.
    """
    template_path = Path(input_path)

    try:
        template_text = template_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise CodegenError(
            f"Unable to read template {template_path}: {error}"
        ) from error

    expanded_text = replace_placeholders(template_text, template_path, catalogs)
    document = parse_json_document(expanded_text, template_path)

    return render_json_document(document)


def generate_json_file(
    input_path: Path,
    output_path: Path,
    catalogs: Sequence[Path] | None = None,
) -> None:
    """Generate a JSON file, creating its parent directory when necessary."""
    destination = Path(output_path)
    generated_text = generate_json_text(Path(input_path), catalogs)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(generated_text, encoding="utf-8", newline="\n")
    except (OSError, UnicodeError) as error:
        raise CodegenError(
            f"Unable to write generated JSON to {destination}: {error}"
        ) from error
