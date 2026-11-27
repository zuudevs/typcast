"""Unit tests for the fluent builder of the Python SDK.

The tests cover the contract of `docs/specifications/sdk-api.md`: the surface
of the builder, the normalization of the content, the defaults of the node
catalog, the errors of the diagnostic taxonomy, and the immutability of the
snapshot that `build()` returns.

Usage:

    bazel test //packages/python/tests:builder_tests
"""

from __future__ import annotations

import unittest

from typcast import (
    ApiUsageError,
    Bold,
    Diagnostic,
    Document,
    DocumentBuilder,
    Italic,
    Length,
    Link,
    ListBlock,
    Margin,
    Module,
    Monospace,
    RawBlock,
    RawSpan,
    Table,
    TableColumn,
    Text,
    TypcastError,
    ValidationError,
    bold,
    cell,
    column,
    italic,
    line_break,
    link,
    monospace,
    raw_inline,
    text,
)


def codes(diagnostics: tuple[Diagnostic, ...]) -> list[str]:
    """Returns the codes of the diagnostics."""
    return [diagnostic.code for diagnostic in diagnostics]


def first_diagnostic(error: TypcastError) -> Diagnostic:
    """Returns the first diagnostic of an error."""
    return error.diagnostics[0]


class BuilderSurfaceTests(unittest.TestCase):
    """Checks the surface of the builder and the chaining of its methods."""

    def test_the_builder_needs_no_argument(self) -> None:
        subject = DocumentBuilder()
        self.assertIsInstance(subject, DocumentBuilder)

    def test_every_documented_method_exists(self) -> None:
        for name in (
            "title",
            "author",
            "date",
            "page",
            "heading",
            "paragraph",
            "bullet_list",
            "numbered_list",
            "table",
            "image",
            "page_break",
            "raw",
            "module",
            "build",
        ):
            self.assertTrue(
                callable(getattr(DocumentBuilder, name, None)),
                f"the builder must expose '{name}'",
            )

    def test_every_span_helper_exists(self) -> None:
        for helper in (
            text,
            bold,
            italic,
            monospace,
            link,
            line_break,
            raw_inline,
        ):
            self.assertTrue(callable(helper))

    def test_every_table_helper_exists(self) -> None:
        self.assertTrue(callable(column))
        self.assertTrue(callable(cell))

    def test_every_mutating_method_returns_the_builder(self) -> None:
        subject = DocumentBuilder()
        self.assertIs(subject.title("Title"), subject)
        self.assertIs(subject.author("Author"), subject)
        self.assertIs(subject.date("2026-11-24"), subject)
        self.assertIs(subject.page(), subject)
        self.assertIs(subject.heading(1, "Heading"), subject)
        self.assertIs(subject.paragraph("Body"), subject)
        self.assertIs(subject.bullet_list(["Item"]), subject)
        self.assertIs(subject.numbered_list(["Item"]), subject)
        self.assertIs(subject.table(columns=[column("A")], rows=[[["x"]]]), subject)
        self.assertIs(subject.image("a.png", alt="Alt"), subject)
        self.assertIs(subject.page_break(), subject)
        self.assertIs(subject.raw("#value"), subject)
        self.assertIs(subject.module("a.typ"), subject)

    def test_the_documented_example_builds(self) -> None:
        document = (
            DocumentBuilder()
            .title("Quarterly Report")
            .author("Example Corp")
            .date("2026-11-24")
            .page(paper="a4", orientation="portrait", margin=Length.cm(2.0))
            .heading(1, "Quarterly Report")
            .paragraph("Revenue grew by ", bold("12%"), ".")
            .bullet_list(["Revenue", "Cost", "Headcount"])
            .table(
                columns=[
                    column("Metric", align="left"),
                    column("Value", align="right"),
                ],
                rows=[
                    [["Revenue"], ["1,200"]],
                    [["Cost"], ["800"]],
                ],
            )
            .image(
                "figures/revenue.png",
                alt="Revenue chart",
                caption="Figure 1",
            )
            .page_break()
            .raw(
                '#figure(image("logo.png"), caption: [Logo])',
                format="markup",
            )
            .module("modules/format.typ", items=["currency"])
            .build()
        )
        self.assertIsInstance(document, Document)
        self.assertEqual(len(document.contents), 7)
        self.assertEqual(len(document.modules), 1)

    def test_the_blocks_keep_the_order_of_the_calls(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .heading(1, "First")
            .paragraph("Second")
            .page_break()
            .build()
        )
        self.assertEqual(
            [block.type for block in document.contents],
            ["heading", "paragraph", "pageBreak"],
        )

    def test_the_modules_keep_the_order_of_the_calls(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .paragraph("Body")
            .module("a.typ", alias="first")
            .module("b.typ", alias="second")
            .build()
        )
        self.assertEqual(
            [module.path for module in document.modules],
            ["a.typ", "b.typ"],
        )


class ContentNormalizationTests(unittest.TestCase):
    """Checks the normalization of the content of the builder."""

    def test_a_string_becomes_a_text_span(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        paragraph = document.contents[0]
        self.assertEqual(paragraph.content, (Text("Body"),))

    def test_a_span_is_kept(self) -> None:
        document = (
            DocumentBuilder().title("Title").paragraph(bold("Body")).build()
        )
        paragraph = document.contents[0]
        self.assertEqual(paragraph.content, (Bold((Text("Body"),)),))

    def test_the_order_of_the_content_is_kept(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .paragraph("A ", bold("B"), " C")
            .build()
        )
        paragraph = document.contents[0]
        self.assertEqual(
            paragraph.content,
            (Text("A "), Bold((Text("B"),)), Text(" C")),
        )

    def test_two_strings_are_not_merged(self) -> None:
        document = (
            DocumentBuilder().title("Title").paragraph("A", "B").build()
        )
        paragraph = document.contents[0]
        self.assertEqual(paragraph.content, (Text("A"), Text("B")))

    def test_the_emphasis_nests(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .paragraph(bold("A", italic("B")))
            .build()
        )
        paragraph = document.contents[0]
        self.assertEqual(
            paragraph.content,
            (Bold((Text("A"), Italic((Text("B"),)))),),
        )

    def test_a_list_item_is_normalized(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .bullet_list(["Plain", ["Mixed ", bold("bold")]])
            .build()
        )
        block = document.contents[0]
        self.assertEqual(
            block.items,
            (
                (Text("Plain"),),
                (Text("Mixed "), Bold((Text("bold"),))),
            ),
        )

    def test_a_table_header_is_normalized(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .table(columns=[column("Metric")], rows=[[["1,200"]]])
            .build()
        )
        table = document.contents[0]
        self.assertEqual(table.columns[0].header, (Text("Metric"),))

    def test_a_table_cell_is_normalized(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .table(
                columns=[column("Metric")],
                rows=[[cell("Revenue ", bold("12%"))]],
            )
            .build()
        )
        table = document.contents[0]
        self.assertEqual(
            table.rows[0][0],
            (Text("Revenue "), Bold((Text("12%"),))),
        )

    def test_an_empty_table_cell_is_kept(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .table(columns=[column("Metric")], rows=[[[]]])
            .build()
        )
        table = document.contents[0]
        self.assertEqual(table.rows[0][0], ())

    def test_an_image_caption_is_normalized(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .image("a.png", alt="Alt", caption="Figure 1")
            .build()
        )
        image = document.contents[0]
        self.assertEqual(image.caption, (Text("Figure 1"),))

    def test_a_link_content_is_normalized(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .paragraph(link("https://example.com", "Example"))
            .build()
        )
        paragraph = document.contents[0]
        self.assertEqual(
            paragraph.content,
            (Link("https://example.com", (Text("Example"),)),),
        )

    def test_the_helpers_produce_the_model_spans(self) -> None:
        self.assertIsInstance(text("A"), Text)
        self.assertIsInstance(bold("A"), Bold)
        self.assertIsInstance(italic("A"), Italic)
        self.assertIsInstance(monospace("A"), Monospace)
        self.assertIsInstance(link("u", "A"), Link)
        self.assertIsInstance(line_break(), type(line_break()))
        self.assertIsInstance(raw_inline("x", "code"), RawSpan)
        self.assertIsInstance(column("A"), TableColumn)


class DefaultTests(unittest.TestCase):
    """Checks the defaults that the node catalog names."""

    def test_the_default_page_is_a4_portrait(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        self.assertEqual(document.page.paper, "a4")
        self.assertEqual(document.page.orientation, "portrait")

    def test_the_default_margin_is_two_and_a_half_centimeters(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        for side in (
            document.page.margin.top,
            document.page.margin.right,
            document.page.margin.bottom,
            document.page.margin.left,
        ):
            self.assertEqual(side, Length.cm(2.5))

    def test_a_bullet_list_is_unordered(self) -> None:
        document = (
            DocumentBuilder().title("Title").bullet_list(["Item"]).build()
        )
        block = document.contents[0]
        self.assertIsInstance(block, ListBlock)
        self.assertFalse(block.ordered)

    def test_a_numbered_list_is_ordered(self) -> None:
        document = (
            DocumentBuilder().title("Title").numbered_list(["Item"]).build()
        )
        block = document.contents[0]
        self.assertTrue(block.ordered)

    def test_the_modules_are_empty_by_default(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        self.assertEqual(document.modules, ())

    def test_an_image_without_a_caption_holds_no_caption(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .image("a.png", alt="Alt")
            .build()
        )
        image = document.contents[0]
        self.assertIsNone(image.caption)
        self.assertNotIn("caption", image.to_dict())

    def test_an_image_without_a_width_holds_no_width(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .image("a.png", alt="Alt")
            .build()
        )
        image = document.contents[0]
        self.assertIsNone(image.width)
        self.assertNotIn("width", image.to_dict())

    def test_the_metadata_holds_no_author_and_no_date_by_default(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        self.assertIsNone(document.metadata.author)
        self.assertIsNone(document.metadata.date)
        value = document.to_dict()
        self.assertNotIn("author", value["metadata"])
        self.assertNotIn("date", value["metadata"])

    def test_a_uniform_margin_is_the_margin_of_every_side(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .page(margin=Length.cm(2.0))
            .paragraph("Body")
            .build()
        )
        margin = document.page.margin
        self.assertEqual(margin.top, Length.cm(2.0))
        self.assertEqual(margin.right, Length.cm(2.0))
        self.assertEqual(margin.bottom, Length.cm(2.0))
        self.assertEqual(margin.left, Length.cm(2.0))

    def test_a_margin_names_every_side(self) -> None:
        margin = Margin(
            top=Length.cm(1.0),
            right=Length.cm(2.0),
            bottom=Length.cm(3.0),
            left=Length.cm(4.0),
        )
        document = (
            DocumentBuilder()
            .title("Title")
            .page(margin=margin)
            .paragraph("Body")
            .build()
        )
        self.assertEqual(document.page.margin, margin)

    def test_the_canonical_json_holds_the_defaults(self) -> None:
        document = DocumentBuilder().title("Title").paragraph("Body").build()
        value = document.to_dict()
        self.assertEqual(value["page"]["paper"], "a4")
        self.assertEqual(value["page"]["orientation"], "portrait")
        self.assertEqual(
            value["page"]["margin"]["top"],
            {"value": 2.5, "unit": "cm"},
        )
        self.assertEqual(value["modules"], [])


class ValidationTests(unittest.TestCase):
    """Checks the errors that the builder reports."""

    def assert_error(
        self,
        code: str,
        phase: str,
        path: str,
        factory,
        error_type: type[TypcastError] = ValidationError,
    ) -> TypcastError:
        """Runs a factory and checks the diagnostic of its error."""
        with self.assertRaises(error_type) as context:
            factory()
        error = context.exception
        diagnostic = first_diagnostic(error)
        self.assertEqual(diagnostic.code, code)
        self.assertEqual(diagnostic.severity, "error")
        self.assertEqual(diagnostic.phase, phase)
        self.assertEqual(diagnostic.path, path)
        self.assertIsInstance(error, TypcastError)
        return error

    def test_a_missing_title_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0001",
            "validation",
            "/metadata/title",
            lambda: DocumentBuilder().build(),
        )

    def test_a_document_without_content_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0006",
            "validation",
            "/contents",
            lambda: DocumentBuilder().title("Title").build(),
        )

    def test_an_empty_heading_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0006",
            "validation",
            "/contents/0/content",
            lambda: DocumentBuilder().title("Title").heading(1),
        )

    def test_an_empty_paragraph_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0006",
            "validation",
            "/contents/0/content",
            lambda: DocumentBuilder().title("Title").paragraph(),
        )

    def test_an_empty_list_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0006",
            "validation",
            "/contents/0/items",
            lambda: DocumentBuilder().title("Title").bullet_list([]),
        )

    def test_an_empty_list_item_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0006",
            "validation",
            "/contents/0/items/0",
            lambda: DocumentBuilder().title("Title").bullet_list([[]]),
        )

    def test_a_table_with_too_few_cells_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0007",
            "validation",
            "/contents/0/rows/0",
            lambda: DocumentBuilder()
            .title("Title")
            .table(columns=[column("A"), column("B")], rows=[[["x"]]])
            .build(),
        )

    def test_a_table_with_too_many_cells_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0007",
            "validation",
            "/contents/0/rows/0",
            lambda: DocumentBuilder()
            .title("Title")
            .table(columns=[column("A")], rows=[[["x"], ["y"]]])
            .build(),
        )

    def test_a_duplicated_module_alias_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0008",
            "validation",
            "/modules/1/alias",
            lambda: DocumentBuilder()
            .title("Title")
            .paragraph("Body")
            .module("a.typ", alias="report")
            .module("b.typ", alias="report")
            .build(),
        )

    def test_a_module_alias_and_items_are_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0009",
            "validation",
            "/modules/0/alias",
            lambda: DocumentBuilder()
            .title("Title")
            .module("a.typ", alias="report", items=["currency"]),
        )

    def test_an_invalid_module_alias_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0008",
            "validation",
            "/modules/0/alias",
            lambda: DocumentBuilder()
            .title("Title")
            .module("a.typ", alias="1report"),
        )

    def test_a_raw_node_at_the_limit_is_accepted(self) -> None:
        document = (
            DocumentBuilder()
            .title("Title")
            .raw("x" * 1_048_576)
            .build()
        )
        block = document.contents[0]
        self.assertIsInstance(block, RawBlock)
        self.assertEqual(len(block.value), 1_048_576)

    def test_a_raw_node_over_the_limit_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0010",
            "validation",
            "/contents/0/value",
            lambda: DocumentBuilder()
            .title("Title")
            .raw("x" * 1_048_577)
            .build(),
        )

    def test_a_heading_level_outside_the_range_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0005",
            "validation",
            "/contents/0/level",
            lambda: DocumentBuilder().title("Title").heading(7, "Heading"),
        )

    def test_an_invalid_alignment_is_rejected(self) -> None:
        # The column helper builds the model on its own, so the path of the
        # diagnostic names the field of the column and not the table.
        self.assert_error(
            "TYPCAST-VAL-0003",
            "validation",
            "/align",
            lambda: DocumentBuilder()
            .title("Title")
            .table(columns=[column("A", "middle")], rows=[[["x"]]]),
        )

    def test_an_invalid_raw_format_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0003",
            "validation",
            "/contents/0/format",
            lambda: DocumentBuilder().title("Title").raw("x", format="latex"),
        )

    def test_an_invalid_date_is_rejected(self) -> None:
        self.assert_error(
            "TYPCAST-VAL-0011",
            "validation",
            "/metadata/date",
            lambda: DocumentBuilder()
            .title("Title")
            .date("2026-13-01")
            .build(),
        )

    def test_a_title_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/metadata/title",
            lambda: DocumentBuilder().title(42),
            ApiUsageError,
        )

    def test_content_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/contents/0/content/0",
            lambda: DocumentBuilder().title("Title").paragraph(42),
            ApiUsageError,
        )

    def test_a_level_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/contents/0/level",
            lambda: DocumentBuilder().title("Title").heading("1", "Heading"),
            ApiUsageError,
        )

    def test_a_margin_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/page/margin",
            lambda: DocumentBuilder().title("Title").page(margin=42),
            ApiUsageError,
        )

    def test_a_column_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/contents/0/columns/0",
            lambda: DocumentBuilder()
            .title("Title")
            .table(columns=["Metric"], rows=[[["x"]]]),
            ApiUsageError,
        )

    def test_an_item_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/contents/0/items/0",
            lambda: DocumentBuilder().title("Title").bullet_list([42]),
            ApiUsageError,
        )

    def test_a_module_item_of_the_wrong_type_is_an_api_error(self) -> None:
        self.assert_error(
            "TYPCAST-API-0001",
            "api",
            "/modules/0/items/0",
            lambda: DocumentBuilder()
            .title("Title")
            .module("a.typ", items=[42]),
            ApiUsageError,
        )

    def test_the_error_carries_every_diagnostic(self) -> None:
        with self.assertRaises(ValidationError) as context:
            (
                DocumentBuilder()
                .title("Title")
                .table(columns=[column("A"), column("B")], rows=[[["x"]]])
                .module("a.typ", alias="report")
                .module("b.typ", alias="report")
                .build()
            )
        error = context.exception
        self.assertEqual(
            codes(error.diagnostics),
            ["TYPCAST-VAL-0007", "TYPCAST-VAL-0008"],
        )
        self.assertEqual(
            [diagnostic.path for diagnostic in error.diagnostics],
            ["/contents/0/rows/0", "/modules/1/alias"],
        )
        self.assertEqual(str(error), error.diagnostics[0].message)

    def test_the_api_error_carries_a_diagnostic(self) -> None:
        with self.assertRaises(ApiUsageError) as context:
            DocumentBuilder().title(42)
        error = context.exception
        self.assertEqual(len(error.diagnostics), 1)
        self.assertEqual(error.diagnostics[0].code, "TYPCAST-API-0001")
        self.assertEqual(error.diagnostics[0].phase, "api")

    def test_the_builder_does_not_change_when_a_call_fails(self) -> None:
        builder = DocumentBuilder().title("Title")
        with self.assertRaises(ApiUsageError):
            builder.paragraph(42)
        document = builder.paragraph("Body").build()
        self.assertEqual(len(document.contents), 1)


class SnapshotTests(unittest.TestCase):
    """Checks the immutability of the snapshot that `build()` returns."""

    def test_a_later_call_does_not_change_a_built_document(self) -> None:
        builder = DocumentBuilder().title("Title").paragraph("First")
        document = builder.build()
        before = document.to_json()
        builder.paragraph("Second").title("Another title")
        self.assertEqual(document.to_json(), before)
        self.assertEqual(len(document.contents), 1)

    def test_two_builds_of_one_builder_are_independent(self) -> None:
        builder = DocumentBuilder().title("Title").paragraph("First")
        first = builder.build()
        builder.paragraph("Second")
        second = builder.build()
        self.assertEqual(len(first.contents), 1)
        self.assertEqual(len(second.contents), 2)
        self.assertNotEqual(first.to_json(), second.to_json())

    def test_a_caller_cannot_change_a_document_with_an_input_list(self) -> None:
        items = ["First"]
        builder = DocumentBuilder().title("Title").bullet_list(items)
        document = builder.build()
        before = document.to_json()
        items.append("Second")
        self.assertEqual(document.to_json(), before)

    def test_a_caller_cannot_change_a_document_with_an_input_row(self) -> None:
        rows = [[["First"]]]
        builder = (
            DocumentBuilder()
            .title("Title")
            .table(columns=[column("A")], rows=rows)
        )
        document = builder.build()
        before = document.to_json()
        rows[0].append(["Second"])
        rows[0][0].append("Changed")
        self.assertEqual(document.to_json(), before)

    def test_a_caller_cannot_change_a_document_with_an_input_column(self) -> None:
        columns = [column("A")]
        builder = (
            DocumentBuilder()
            .title("Title")
            .table(columns=columns, rows=[[["x"]]])
        )
        document = builder.build()
        before = document.to_json()
        columns.append(column("B"))
        self.assertEqual(document.to_json(), before)

    def test_a_caller_cannot_change_a_document_with_an_input_item(self) -> None:
        items = [["First", bold("bold")]]
        builder = DocumentBuilder().title("Title").bullet_list(items)
        document = builder.build()
        before = document.to_json()
        items[0].append("Changed")
        self.assertEqual(document.to_json(), before)


if __name__ == "__main__":
    unittest.main()
