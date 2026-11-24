import json
import tempfile
import unittest
from pathlib import Path

from typcast_codegen.errors import CodegenError
from typcast_codegen.pipeline import generate_json_file, generate_json_text


class JsonTemplateGeneratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_replaces_csv_column_relative_to_template(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text(
            "Value,Details\nalpha,First value\nbeta,Second value\n",
            encoding="utf-8",
        )

        template = self.root / "schema.json.tmpl"
        template.write_text(
            '{"type": "string", "enum": <./values.csv:Value>}',
            encoding="utf-8",
        )

        generated = generate_json_text(template)

        self.assertEqual(
            json.loads(generated),
            {"type": "string", "enum": ["alpha", "beta"]},
        )

    def test_template_without_placeholder_is_validated(self) -> None:
        template = self.root / "plain.json.tmpl"
        template.write_text('{"type": "string"}', encoding="utf-8")

        self.assertEqual(
            json.loads(generate_json_text(template)),
            {"type": "string"},
        )

    def test_missing_csv_column_reports_an_error(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text("Value\nalpha\n", encoding="utf-8")

        template = self.root / "schema.json.tmpl"
        template.write_text('{"enum": <./values.csv:Missing>}', encoding="utf-8")

        with self.assertRaisesRegex(CodegenError, "was not found"):
            generate_json_text(template)

    def test_empty_value_in_selected_column_reports_an_error(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text(
            "Value,Details\nalpha,First value\n,Details without a value\n",
            encoding="utf-8",
        )

        template = self.root / "schema.json.tmpl"
        template.write_text('{"enum": <./values.csv:Value>}', encoding="utf-8")

        with self.assertRaisesRegex(CodegenError, "empty value"):
            generate_json_text(template)

    def test_fully_blank_rows_are_skipped(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text(
            "Value,Details\nalpha,First value\n,\nbeta,Second value\n",
            encoding="utf-8",
        )

        template = self.root / "schema.json.tmpl"
        template.write_text('{"enum": <./values.csv:Value>}', encoding="utf-8")

        self.assertEqual(
            json.loads(generate_json_text(template)),
            {"enum": ["alpha", "beta"]},
        )

    def test_invalid_json_reports_an_error(self) -> None:
        template = self.root / "invalid.json.tmpl"
        template.write_text('{"type": "string",}', encoding="utf-8")

        with self.assertRaisesRegex(CodegenError, "invalid JSON"):
            generate_json_text(template)

    def test_output_parent_directory_is_created(self) -> None:
        template = self.root / "schema.json.tmpl"
        template.write_text('{"type": "string"}', encoding="utf-8")
        output = self.root / "nested" / "out" / "schema.json"

        generate_json_file(template, output)

        self.assertTrue(output.is_file())
        self.assertEqual(
            json.loads(output.read_text(encoding="utf-8")),
            {"type": "string"},
        )


if __name__ == "__main__":
    unittest.main()
