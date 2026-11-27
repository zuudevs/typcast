"""Unit tests of the enum generator."""

import tempfile
import unittest
from pathlib import Path

from typcast_enumgen.catalog import read_catalog_column
from typcast_enumgen.cli import main
from typcast_enumgen.errors import EnumgenError
from typcast_enumgen.renderers import render_python, render_typescript


class CatalogReaderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_catalog(self, text: str, name: str = "values.csv") -> Path:
        catalog = self.root / name
        catalog.write_text(text, encoding="utf-8")
        return catalog

    def test_reads_the_values_of_the_requested_column(self) -> None:
        catalog = self.write_catalog("Value,Details\nalpha,First\nbeta,Second\n")

        self.assertEqual(
            read_catalog_column(catalog, "Value"),
            ["alpha", "beta"],
        )

    def test_accepts_a_byte_order_mark(self) -> None:
        catalog = self.write_catalog("Value,Details\nalpha,First\n")
        catalog.write_bytes(b"\xef\xbb\xbf" + catalog.read_bytes())

        self.assertEqual(read_catalog_column(catalog, "Value"), ["alpha"])

    def test_skips_a_fully_blank_row(self) -> None:
        catalog = self.write_catalog("Value,Details\nalpha,First\n,\n")

        self.assertEqual(read_catalog_column(catalog, "Value"), ["alpha"])

    def test_rejects_an_empty_value_beside_another_value(self) -> None:
        catalog = self.write_catalog("Value,Details\nalpha,First\n,Second\n")

        with self.assertRaisesRegex(EnumgenError, "empty value"):
            read_catalog_column(catalog, "Value")

    def test_rejects_an_empty_value_in_the_requested_column(self) -> None:
        catalog = self.write_catalog("Value,Details\nalpha,First\n,Second\n")

        with self.assertRaisesRegex(EnumgenError, "empty value"):
            read_catalog_column(catalog, "Value")

    def test_rejects_a_missing_column(self) -> None:
        catalog = self.write_catalog("Value\nalpha\n")

        with self.assertRaisesRegex(EnumgenError, "was not found"):
            read_catalog_column(catalog, "Missing")

    def test_rejects_a_file_without_a_header(self) -> None:
        catalog = self.write_catalog("")

        with self.assertRaisesRegex(EnumgenError, "no header"):
            read_catalog_column(catalog, "Value")

    def test_rejects_a_catalog_without_values(self) -> None:
        catalog = self.write_catalog("Value,Details\n")

        with self.assertRaisesRegex(EnumgenError, "does not contain any values"):
            read_catalog_column(catalog, "Value")

    def test_rejects_a_duplicate_value(self) -> None:
        catalog = self.write_catalog("Value\nalpha\nalpha\n")

        with self.assertRaisesRegex(EnumgenError, "duplicate"):
            read_catalog_column(catalog, "Value")

    def test_rejects_a_missing_file(self) -> None:
        with self.assertRaisesRegex(EnumgenError, "Unable to read"):
            read_catalog_column(self.root / "missing.csv", "Value")


class RendererTests(unittest.TestCase):
    def test_renders_a_typescript_constant(self) -> None:
        rendered = render_typescript(
            ["a4", "a5"],
            "PAPER_VARIANTS",
            "specs/catalogs/enums/paper-variants.csv",
        )

        self.assertIn("export const PAPER_VARIANTS: readonly string[] = [", rendered)
        self.assertIn('  "a4",', rendered)
        self.assertIn('  "a5",', rendered)
        self.assertIn("This file is generated.", rendered)
        self.assertTrue(rendered.endswith("\n"))

    def test_renders_a_python_constant(self) -> None:
        rendered = render_python(
            ["a4", "a5"],
            "PAPER_VARIANTS",
            "specs/catalogs/enums/paper-variants.csv",
        )

        self.assertIn("PAPER_VARIANTS: tuple[str, ...] = (", rendered)
        self.assertIn('    "a4",', rendered)
        self.assertIn("This file is generated.", rendered)
        self.assertTrue(rendered.endswith("\n"))

    def test_escapes_a_value_that_holds_a_quote(self) -> None:
        rendered = render_typescript(['a"b'], "VALUES", "catalog.csv")

        self.assertIn('  "a\\"b",', rendered)

    def test_keeps_a_non_ascii_value(self) -> None:
        rendered = render_typescript(["fr-carré"], "VALUES", "catalog.csv")

        self.assertIn('  "fr-carré",', rendered)

    def test_rejects_a_name_that_is_not_an_identifier(self) -> None:
        with self.assertRaisesRegex(EnumgenError, "identifier"):
            render_typescript(["a4"], "paper variants", "catalog.csv")

    def test_rejects_a_name_that_is_not_upper_case(self) -> None:
        with self.assertRaisesRegex(EnumgenError, "upper case"):
            render_typescript(["a4"], "PaperVariants", "catalog.csv")

    def test_rejects_an_empty_name(self) -> None:
        with self.assertRaisesRegex(EnumgenError, "must not be empty"):
            render_typescript(["a4"], "", "catalog.csv")


class CommandLineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_writes_the_generated_file(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text("Value\nalpha\n", encoding="utf-8")
        output = self.root / "out" / "values.ts"

        code = main(
            [
                "--catalog",
                str(catalog),
                "--column",
                "Value",
                "--name",
                "VALUES",
                "--language",
                "typescript",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn('  "alpha",', output.read_text(encoding="utf-8"))

    def test_reports_an_error_of_the_catalog(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text("Value\n", encoding="utf-8")
        output = self.root / "out" / "values.ts"

        code = main(
            [
                "--catalog",
                str(catalog),
                "--column",
                "Value",
                "--name",
                "VALUES",
                "--language",
                "typescript",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 1)
        self.assertFalse(output.exists())

    def test_writes_the_python_target(self) -> None:
        catalog = self.root / "values.csv"
        catalog.write_text("Value\nalpha\n", encoding="utf-8")
        output = self.root / "out" / "values.py"

        code = main(
            [
                "--catalog",
                str(catalog),
                "--column",
                "Value",
                "--name",
                "VALUES",
                "--language",
                "python",
                "--output",
                str(output),
            ]
        )

        self.assertEqual(code, 0)
        self.assertIn('    "alpha",', output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
