"""Unit tests for the validation engine of the Python SDK.

The tests cover the semantic rules of `docs/specifications/document-ir.md`:
the shape of a table, the uniqueness of a module alias, and the size of a raw
node. They also cover the configuration of the raw size limit and the order
of the diagnostics.

Usage:

    bazel test //packages/python/tests:validation_tests
"""

from __future__ import annotations

import unittest

from typcast import (
    Bold,
    ConfigError,
    Diagnostic,
    Document,
    Heading,
    Image,
    Italic,
    Length,
    Link,
    ListBlock,
    Margin,
    Metadata,
    Module,
    Monospace,
    Page,
    Paragraph,
    RawBlock,
    RawSpan,
    Table,
    TableColumn,
    Text,
    TypcastConfig,
    TypcastError,
    validate_document,
)
from typcast.validations.encoding import utf8_length

PAGE = Page(
    paper="a4",
    orientation="portrait",
    margin=Margin(
        top=Length(2, "cm"),
        right=Length(2, "cm"),
        bottom=Length(2, "cm"),
        left=Length(2, "cm"),
    ),
)


def document(contents, modules=()) -> Document:
    """Returns a document with the given contents and modules."""
    return Document(
        metadata=Metadata(title="Title"),
        page=PAGE,
        contents=contents,
        modules=modules,
    )


def paragraph(*values: str) -> Paragraph:
    """Returns a paragraph with one text span per value."""
    return Paragraph(content=[Text(value) for value in values])


def table(columns: int, rows: list[int]) -> Table:
    """Returns a table with the given column count and cell counts per row."""
    return Table(
        columns=[
            TableColumn(header=[Text(f"Column {index}")], align="left")
            for index in range(columns)
        ],
        rows=[
            [[Text(f"Cell {cell}")] for cell in range(count)]
            for count in rows
        ],
    )


def codes(diagnostics: tuple[Diagnostic, ...]) -> list[str]:
    """Returns the codes of the diagnostics."""
    return [diagnostic.code for diagnostic in diagnostics]


class ValidationTests(unittest.TestCase):
    """Checks the semantic rules of the validation engine."""

    def test_a_valid_document_reports_no_diagnostic(self) -> None:
        subject = document([paragraph("Body")])
        self.assertEqual(subject.validate(), ())

    def test_the_method_and_the_function_agree(self) -> None:
        subject = document([paragraph("Body")], [Module(path="a.typ", alias="a")])
        self.assertEqual(subject.validate(), validate_document(subject))

    def test_the_engine_reports_every_problem(self) -> None:
        subject = document(
            [
                table(2, [2, 1, 3]),
                Paragraph(content=[RawSpan(format="code", value="12345")]),
            ],
            [
                Module(path="a.typ", alias="report"),
                Module(path="b.typ", alias="report"),
            ],
        )
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=4))
        self.assertEqual(
            codes(diagnostics),
            [
                "TYPCAST-VAL-0007",
                "TYPCAST-VAL-0007",
                "TYPCAST-VAL-0010",
                "TYPCAST-VAL-0008",
            ],
        )

    def test_the_diagnostics_come_in_the_order_of_the_document(self) -> None:
        subject = document(
            [
                Paragraph(content=[RawSpan(format="code", value="12345")]),
                table(1, [2]),
            ],
            [Module(path="a.typ", alias="x"), Module(path="b.typ", alias="x")],
        )
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=4))
        self.assertEqual(
            [diagnostic.path for diagnostic in diagnostics],
            [
                "/contents/0/content/0/value",
                "/contents/1/rows/0",
                "/modules/1/alias",
            ],
        )

    def test_the_engine_raises_no_error_for_a_semantic_problem(self) -> None:
        subject = document([table(2, [1])])
        # The call must return the diagnostics instead of raising an error.
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 1)
        self.assertIsInstance(diagnostics, tuple)

    def test_a_table_row_with_too_few_cells_is_reported(self) -> None:
        subject = document([table(2, [2, 1])])
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-VAL-0007")
        self.assertEqual(diagnostic.path, "/contents/0/rows/1")
        self.assertEqual(
            diagnostic.message,
            "'/contents/0/rows/1' must hold 2 cells, got 1.",
        )
        self.assertEqual(dict(diagnostic.details), {"columns": 2, "cells": 1})
        self.assertEqual(diagnostic.severity, "error")
        self.assertEqual(diagnostic.phase, "validation")

    def test_a_table_row_with_too_many_cells_is_reported(self) -> None:
        subject = document([table(1, [2])])
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].code, "TYPCAST-VAL-0007")
        self.assertEqual(diagnostics[0].path, "/contents/0/rows/0")
        self.assertEqual(
            dict(diagnostics[0].details),
            {"columns": 1, "cells": 2},
        )

    def test_every_broken_row_of_a_table_is_reported(self) -> None:
        subject = document([table(2, [1, 3, 2])])
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(
            [diagnostic.path for diagnostic in diagnostics],
            ["/contents/0/rows/0", "/contents/0/rows/1"],
        )

    def test_a_duplicated_module_alias_is_reported(self) -> None:
        subject = document(
            [paragraph("Body")],
            [
                Module(path="a.typ", alias="report"),
                Module(path="b.typ", alias="report"),
            ],
        )
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-VAL-0008")
        self.assertEqual(diagnostic.path, "/modules/1/alias")
        self.assertEqual(
            diagnostic.message,
            "'/modules/1/alias' is already used by the module at '/modules/0/alias'.",
        )
        self.assertEqual(
            dict(diagnostic.details),
            {"alias": "report", "duplicateOf": "/modules/0/alias"},
        )

    def test_every_duplicated_alias_is_reported(self) -> None:
        subject = document(
            [paragraph("Body")],
            [
                Module(path="a.typ", alias="report"),
                Module(path="b.typ", alias="report"),
                Module(path="c.typ", alias="report"),
            ],
        )
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 2)
        self.assertEqual(
            [diagnostic.path for diagnostic in diagnostics],
            ["/modules/1/alias", "/modules/2/alias"],
        )
        # Every duplicate names the first use of the alias.
        self.assertEqual(
            dict(diagnostics[1].details)["duplicateOf"],
            "/modules/0/alias",
        )

    def test_distinct_module_aliases_are_accepted(self) -> None:
        subject = document(
            [paragraph("Body")],
            [
                Module(path="a.typ", alias="first"),
                Module(path="b.typ", alias="second"),
            ],
        )
        self.assertEqual(subject.validate(), ())

    def test_a_module_that_names_no_alias_takes_no_part(self) -> None:
        # A module that names no alias takes the name of its file, which the
        # asset layer resolves, so the engine cannot compare it.
        subject = document(
            [paragraph("Body")],
            [
                Module(path="report.typ"),
                Module(path="summary.typ"),
                Module(path="format.typ", items=["currency"]),
            ],
        )
        self.assertEqual(subject.validate(), ())

    def test_a_raw_value_at_the_limit_is_accepted(self) -> None:
        subject = document([RawBlock(format="markup", value="12345678")])
        self.assertEqual(subject.validate(TypcastConfig(max_raw_bytes=8)), ())

    def test_a_raw_value_over_the_limit_is_reported(self) -> None:
        subject = document([RawBlock(format="markup", value="123456789")])
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=8))
        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-VAL-0010")
        self.assertEqual(diagnostic.path, "/contents/0/value")
        self.assertEqual(
            diagnostic.message,
            "'/contents/0/value' must not hold more than 8 bytes, got 9.",
        )
        self.assertEqual(dict(diagnostic.details), {"maxBytes": 8, "bytes": 9})

    def test_the_limit_counts_bytes_and_not_code_points(self) -> None:
        # The value holds four code points, but its encoding takes twelve
        # bytes, so a limit of eleven bytes rejects it.
        subject = document([RawBlock(format="markup", value="한글한글")])
        self.assertEqual(subject.validate(TypcastConfig(max_raw_bytes=12)), ())
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=11))
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(dict(diagnostics[0].details), {"maxBytes": 11, "bytes": 12})

    def test_the_default_limit_is_one_mebibyte(self) -> None:
        subject = document([RawBlock(format="markup", value="x" * 1_048_576)])
        self.assertEqual(subject.validate(), ())
        subject = document([RawBlock(format="markup", value="x" * 1_048_577)])
        diagnostics = subject.validate()
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(
            dict(diagnostics[0].details),
            {"maxBytes": 1_048_576, "bytes": 1_048_577},
        )

    def test_a_raw_span_in_every_container_is_reported(self) -> None:
        raw = RawSpan(format="code", value="12345")
        cases = [
            ([Paragraph(content=[raw])], ["/contents/0/content/0/value"]),
            ([Heading(level=1, content=[raw])], ["/contents/0/content/0/value"]),
            (
                [ListBlock(ordered=False, items=[[raw]])],
                ["/contents/0/items/0/0/value"],
            ),
            (
                [
                    Paragraph(
                        content=[
                            Bold(content=[raw]),
                            Italic(content=[raw]),
                            Monospace(content=[raw]),
                            Link(href="https://example.com", content=[raw]),
                        ]
                    )
                ],
                [
                    "/contents/0/content/0/content/0/value",
                    "/contents/0/content/1/content/0/value",
                    "/contents/0/content/2/content/0/value",
                    "/contents/0/content/3/content/0/value",
                ],
            ),
            (
                [Image(path="a.png", alt="A", caption=[raw])],
                ["/contents/0/caption/0/value"],
            ),
        ]
        for blocks, paths in cases:
            with self.subTest(paths=paths):
                subject = document(blocks)
                diagnostics = subject.validate(TypcastConfig(max_raw_bytes=4))
                self.assertEqual(
                    [diagnostic.path for diagnostic in diagnostics],
                    paths,
                )
                for diagnostic in diagnostics:
                    self.assertEqual(diagnostic.code, "TYPCAST-VAL-0010")

    def test_a_raw_span_in_a_table_cell_is_reported(self) -> None:
        subject = document(
            [
                Table(
                    columns=[TableColumn(header=[Text("A")], align="left")],
                    rows=[[[RawSpan(format="code", value="12345")]]],
                )
            ]
        )
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=4))
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].path, "/contents/0/rows/0/0/0/value")

    def test_a_raw_span_in_a_column_header_is_reported(self) -> None:
        subject = document(
            [
                Table(
                    columns=[
                        TableColumn(
                            header=[RawSpan(format="code", value="12345")],
                            align="left",
                        )
                    ],
                    rows=[[[Text("Cell")]]],
                )
            ]
        )
        diagnostics = subject.validate(TypcastConfig(max_raw_bytes=4))
        self.assertEqual(len(diagnostics), 1)
        self.assertEqual(diagnostics[0].path, "/contents/0/columns/0/header/0/value")

    def test_the_engine_rejects_a_value_that_is_not_a_document(self) -> None:
        with self.assertRaises(TypcastError) as caught:
            validate_document("not a document")  # type: ignore[arg-type]
        diagnostic = caught.exception.diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-VAL-0001")
        self.assertEqual(diagnostic.path, "/")
        self.assertEqual(diagnostic.message, "'/' must be a Document.")
        self.assertEqual(dict(diagnostic.details), {"expected": "Document"})

    def test_a_negative_limit_is_rejected(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            TypcastConfig(max_raw_bytes=-1)
        diagnostic = caught.exception.diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-CONFIG-0004")
        self.assertEqual(diagnostic.phase, "config")
        self.assertEqual(diagnostic.path, "/max_raw_bytes")
        self.assertEqual(
            diagnostic.message,
            "'/max_raw_bytes' must not be negative, got '-1'.",
        )
        self.assertEqual(dict(diagnostic.details), {"value": -1})

    def test_a_limit_that_is_not_an_integer_is_rejected(self) -> None:
        for value in (1.5, "8", None, True):
            with self.subTest(value=value):
                with self.assertRaises(ConfigError) as caught:
                    TypcastConfig(max_raw_bytes=value)  # type: ignore[arg-type]
                diagnostic = caught.exception.diagnostics[0]
                self.assertEqual(diagnostic.code, "TYPCAST-CONFIG-0004")
                self.assertEqual(diagnostic.phase, "config")

    def test_a_limit_of_zero_is_accepted(self) -> None:
        self.assertEqual(TypcastConfig(max_raw_bytes=0).max_raw_bytes, 0)

    def test_the_configuration_is_immutable(self) -> None:
        config = TypcastConfig()
        with self.assertRaises(Exception):
            config.max_raw_bytes = 1  # type: ignore[misc]


class Utf8LengthTests(unittest.TestCase):
    """Checks the measurement of the size of a text."""

    def test_an_ascii_text_takes_one_byte_per_character(self) -> None:
        self.assertEqual(utf8_length(""), 0)
        self.assertEqual(utf8_length("abc"), 3)

    def test_a_text_outside_the_basic_plane_takes_four_bytes(self) -> None:
        self.assertEqual(utf8_length("é"), 2)
        self.assertEqual(utf8_length("한"), 3)
        self.assertEqual(utf8_length("😀"), 4)

    def test_a_surrogate_pair_takes_four_bytes(self) -> None:
        self.assertEqual(utf8_length("😀"), 4)

    def test_a_surrogate_that_utf8_cannot_encode_takes_three_bytes(self) -> None:
        self.assertEqual(utf8_length("\ud800"), 3)


if __name__ == "__main__":
    unittest.main()
