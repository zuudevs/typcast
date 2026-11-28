"""Unit tests of the schema generator."""

import json
import tempfile
import unittest
from pathlib import Path

from typcast_schemagen.bundle import read_bundle
from typcast_schemagen.cli import main
from typcast_schemagen.errors import SchemagenError
from typcast_schemagen.renderers import render_python, render_typescript


class BundleReaderTests(unittest.TestCase):
    """Checks the reading of a schema bundle."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, relative: str, document: object) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_reads_every_file_of_the_bundle(self) -> None:
        root = self.write("validator.schema.json", {"type": "object"})
        types = self.write("api/types/paper.schema.json", {"type": "string"})

        documents = read_bundle(
            {
                "validator.schema.json": root,
                "api/types/paper.schema.json": types,
            }
        )

        self.assertEqual(
            list(documents),
            ["api/types/paper.schema.json", "validator.schema.json"],
        )
        self.assertEqual(documents["validator.schema.json"], {"type": "object"})

    def test_rejects_a_bundle_without_a_file(self) -> None:
        with self.assertRaisesRegex(SchemagenError, "holds no schema document"):
            read_bundle({})

    def test_rejects_a_file_that_is_not_json(self) -> None:
        path = self.root / "validator.schema.json"
        path.write_text("{", encoding="utf-8")

        with self.assertRaisesRegex(SchemagenError, "is not valid JSON"):
            read_bundle({"validator.schema.json": path})

    def test_rejects_a_document_that_is_not_an_object(self) -> None:
        path = self.root / "validator.schema.json"
        path.write_text("[]", encoding="utf-8")

        with self.assertRaisesRegex(SchemagenError, "is not a JSON object"):
            read_bundle({"validator.schema.json": path})


class RendererTests(unittest.TestCase):
    """Checks the rendering of a schema bundle."""

    def setUp(self) -> None:
        self.documents = {
            "validator.schema.json": {
                "type": "object",
                "properties": {"title": {"type": "string"}},
                "required": ["title"],
            },
            "api/types/paper.schema.json": {
                "type": "string",
                "enum": ["a4", "a5"],
            },
        }

    def test_the_python_source_holds_the_documents(self) -> None:
        source = render_python(self.documents)
        namespace: dict = {}
        exec(compile(source, "schemas_generated.py", "exec"), namespace)

        self.assertEqual(namespace["SCHEMAS"], self.documents)

    def test_the_python_source_sorts_the_paths(self) -> None:
        source = render_python(self.documents)

        self.assertLess(
            source.index("'api/types/paper.schema.json'"),
            source.index("'validator.schema.json'"),
        )

    def test_the_python_source_escapes_a_quote(self) -> None:
        source = render_python({"a.json": {"description": "a 'quote'"}})
        namespace: dict = {}
        exec(compile(source, "schemas_generated.py", "exec"), namespace)

        self.assertEqual(namespace["SCHEMAS"]["a.json"]["description"], "a 'quote'")

    def test_the_typescript_source_holds_the_documents(self) -> None:
        source = render_typescript(self.documents)

        self.assertIn('"validator.schema.json"', source)
        self.assertIn('"api/types/paper.schema.json"', source)
        self.assertIn("export const SCHEMAS", source)

    def test_the_typescript_source_is_valid_json_inside_the_literal(self) -> None:
        source = render_typescript(self.documents)
        start = source.index("= {") + len("= ")
        end = source.rindex("};") + 1
        literal = source[start:end].strip()

        self.assertEqual(json.loads(literal), self.documents)


class CommandLineTests(unittest.TestCase):
    """Checks the command line of the generator."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "validator.schema.json"
        self.source.write_text(json.dumps({"type": "object"}), encoding="utf-8")
        self.output = self.root / "out" / "schemas_generated.py"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_writes_the_generated_source(self) -> None:
        code = main(
            [
                "--file",
                f"validator.schema.json={self.source}",
                "--language",
                "python",
                "--output",
                str(self.output),
            ]
        )

        self.assertEqual(code, 0)
        self.assertTrue(self.output.is_file())
        self.assertIn("SCHEMAS", self.output.read_text(encoding="utf-8"))

    def test_rejects_an_argument_that_is_not_a_path_and_a_file(self) -> None:
        code = main(
            [
                "--file",
                "validator.schema.json",
                "--language",
                "python",
                "--output",
                str(self.output),
            ]
        )

        self.assertEqual(code, 2)
        self.assertFalse(self.output.exists())

    def test_rejects_a_path_that_the_bundle_names_twice(self) -> None:
        code = main(
            [
                "--file",
                f"validator.schema.json={self.source}",
                "--file",
                f"validator.schema.json={self.source}",
                "--language",
                "python",
                "--output",
                str(self.output),
            ]
        )

        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
