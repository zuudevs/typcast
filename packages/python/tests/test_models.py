"""Unit tests for the immutable document model of the Python SDK.

The tests cover the model-level invariants of `docs/specifications/document-ir.md`:
the immutability of the model, the checks of the constructors, the canonical
JSON form, and the behavior of the reader.

Usage:

    bazel test //packages/python/tests:model_tests
"""

from __future__ import annotations

import dataclasses
import json
import unittest
from typing import Any

from typcast import (
    Bold,
    Document,
    Heading,
    Image,
    Italic,
    Length,
    LineBreak,
    Link,
    ListBlock,
    Margin,
    Metadata,
    Module,
    Monospace,
    Page,
    PageBreak,
    Paragraph,
    RawBlock,
    RawSpan,
    SerializationError,
    Table,
    TableColumn,
    Text,
    TypcastError,
    ValidationError,
)


def margin(value: float | int = 2, unit: str = "cm") -> Margin:
    """Returns a margin with the same length on every side."""
    return Margin(
        top=Length(value, unit),
        right=Length(value, unit),
        bottom=Length(value, unit),
        left=Length(value, unit),
    )


def document(**kwargs: Any) -> Document:
    """Returns a minimal document."""
    arguments: dict[str, Any] = {
        "metadata": Metadata(title="Title"),
        "page": Page(paper="a4", orientation="portrait", margin=margin()),
        "contents": [Paragraph(content=[Text("Body")])],
    }
    arguments.update(kwargs)
    return Document(**arguments)


class ImmutabilityTests(unittest.TestCase):
    """Checks that the model cannot change after its construction."""

    def test_model_fields_are_frozen(self) -> None:
        paragraph = Paragraph(content=[Text("Body")])
        with self.assertRaises(dataclasses.FrozenInstanceError):
            paragraph.content = ()  # type: ignore[misc]

    def test_collections_are_tuples(self) -> None:
        paragraph = Paragraph(content=[Text("Body")])
        self.assertIsInstance(paragraph.content, tuple)

    def test_constructor_copies_the_collection_it_receives(self) -> None:
        content = [Text("Body")]
        paragraph = Paragraph(content=content)
        content.append(Text("Added later"))
        self.assertEqual(len(paragraph.content), 1)

    def test_document_copies_the_contents_it_receives(self) -> None:
        contents = [Paragraph(content=[Text("Body")])]
        built = document(contents=contents)
        contents.append(PageBreak())
        self.assertEqual(len(built.contents), 1)

    def test_nested_models_stay_immutable(self) -> None:
        table = Table(
            columns=[TableColumn(header=[Text("Header")], align="left")],
            rows=[[[Text("Cell")]]],
        )
        self.assertIsInstance(table.columns, tuple)
        self.assertIsInstance(table.columns[0].header, tuple)
        self.assertIsInstance(table.rows, tuple)
        self.assertIsInstance(table.rows[0], tuple)
        self.assertIsInstance(table.rows[0][0], tuple)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            table.columns[0].align = "right"  # type: ignore[misc]

    def test_module_copies_the_items_it_receives(self) -> None:
        items = ["currency"]
        module = Module(path="modules/format.typ", items=items)
        items.append("percent")
        self.assertEqual(module.items, ("currency",))


class ConstructorValidationTests(unittest.TestCase):
    """Checks the model-level invariants of the constructors."""

    def assert_code(self, code: str, factory: Any) -> None:
        with self.assertRaises(ValidationError) as caught:
            factory()
        self.assertEqual(caught.exception.diagnostics[0].code, code)

    def test_empty_title_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0006", lambda: Metadata(title=""))

    def test_invalid_date_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0011",
            lambda: Metadata(title="Title", date="2026-02-30"),
        )

    def test_the_year_zero_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0011",
            lambda: Metadata(title="Title", date="0000-01-01"),
        )

    def test_a_date_below_the_year_100_is_accepted(self) -> None:
        metadata = Metadata(title="Title", date="0001-01-01")
        self.assertEqual(metadata.date, "0001-01-01")
        metadata = Metadata(title="Title", date="0099-12-31")
        self.assertEqual(metadata.date, "0099-12-31")

    def test_a_day_of_a_leap_year_is_accepted(self) -> None:
        metadata = Metadata(title="Title", date="2000-02-29")
        self.assertEqual(metadata.date, "2000-02-29")

    def test_a_day_of_a_century_that_is_not_a_leap_year_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0011",
            lambda: Metadata(title="Title", date="1900-02-29"),
        )

    def test_a_date_with_unicode_digits_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0011",
            lambda: Metadata(title="Title", date="\u0662\u0660\u0662\u0666-01-01"),
        )

    def test_a_date_with_a_trailing_newline_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0011",
            lambda: Metadata(title="Title", date="2026-01-01\n"),
        )

    def test_a_title_of_more_than_512_code_points_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0013",
            lambda: Metadata(title="T" * 513),
        )

    def test_an_author_of_more_than_512_code_points_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0013",
            lambda: Metadata(title="Title", author="A" * 513),
        )

    def test_a_title_of_512_code_points_is_accepted(self) -> None:
        metadata = Metadata(title="T" * 512)
        self.assertEqual(len(metadata.title), 512)

    def test_a_character_outside_the_basic_multilingual_plane_counts_once(self) -> None:
        metadata = Metadata(title="\U0001f600" * 512)
        self.assertEqual(len(metadata.title), 512)
        self.assert_code(
            "TYPCAST-VAL-0013",
            lambda: Metadata(title="\U0001f600" * 513),
        )

    def test_invalid_orientation_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0003",
            lambda: Page(paper="a4", orientation="diagonal", margin=margin()),
        )

    def test_negative_length_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0004", lambda: Length(-1, "cm"))

    def test_unknown_length_unit_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0004", lambda: Length(1, "fr"))

    def test_non_finite_length_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0004", lambda: Length(float("nan"), "cm"))

    def test_invalid_heading_level_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0005",
            lambda: Heading(level=7, content=[Text("Heading")]),
        )

    def test_a_fractional_heading_level_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0001",
            lambda: Heading(level=1.5, content=[Text("Heading")]),
        )

    def test_an_integer_valued_float_heading_level_is_accepted(self) -> None:
        heading = Heading(level=1.0, content=[Text("Heading")])
        self.assertEqual(heading.level, 1)

    def test_a_length_that_the_number_domain_cannot_hold_is_narrowed(self) -> None:
        # The numbers of the IR live in the binary64 domain of ECMAScript, so
        # a Python integer that the domain cannot hold exactly is rounded to
        # the nearest representable value, exactly as TypeScript does.
        length = Length(value=9007199254740993, unit="cm")
        self.assertEqual(length.value, 9007199254740992.0)
        self.assertEqual(length.to_dict()["value"], 9007199254740992)

    def test_a_length_that_overflows_the_number_domain_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0004",
            lambda: Length(value=10**400, unit="cm"),
        )

    def test_empty_content_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0006", lambda: Paragraph(content=[]))

    def test_empty_text_is_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0006", lambda: Text(""))

    def test_invalid_module_alias_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0008",
            lambda: Module(path="modules/report.typ", alias="1report"),
        )

    def test_a_module_alias_with_a_trailing_newline_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0008",
            lambda: Module(path="modules/report.typ", alias="report\n"),
        )

    def test_a_module_item_with_a_trailing_newline_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0008",
            lambda: Module(path="modules/report.typ", items=("summary\n",)),
        )

    def test_the_details_of_a_diagnostic_are_json_serializable(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            Module(path="modules/report.typ", alias=object())  # type: ignore[arg-type]
        diagnostic = caught.exception.diagnostics[0]
        text = json.dumps(diagnostic.to_dict())
        self.assertIn('"value": "object"', text)

    def test_module_alias_and_items_are_exclusive(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0009",
            lambda: Module(
                path="modules/report.typ",
                alias="report",
                items=["currency"],
            ),
        )

    def test_empty_module_items_are_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0006",
            lambda: Module(path="modules/report.typ", items=[]),
        )

    def test_empty_document_contents_are_rejected(self) -> None:
        self.assert_code("TYPCAST-VAL-0006", lambda: document(contents=[]))

    def test_invalid_raw_format_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0003",
            lambda: RawBlock(format="typst", value="value"),
        )

    def test_empty_raw_value_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0006",
            lambda: RawBlock(format="markup", value=""),
        )

    def test_invalid_align_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0003",
            lambda: TableColumn(header=[Text("Header")], align="justify"),
        )

    def test_wrong_argument_type_is_rejected(self) -> None:
        self.assert_code(
            "TYPCAST-VAL-0001",
            lambda: Paragraph(content=[Text("Body"), "not a span"]),  # type: ignore[list-item]
        )

    def test_unsupported_schema_version_is_rejected(self) -> None:
        with self.assertRaises(SerializationError) as caught:
            document(schema_version="2.0.0")
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0002")


class SerializationTests(unittest.TestCase):
    """Checks the canonical JSON form of the document."""

    def test_output_uses_two_space_indentation_and_a_trailing_newline(self) -> None:
        text = document().to_json()
        self.assertTrue(text.endswith("\n"))
        self.assertIn('\n  "schemaVersion": "1.0.0",\n', text)

    def test_output_follows_the_field_order_of_the_contract(self) -> None:
        value = document().to_dict()
        self.assertEqual(
            list(value),
            ["schemaVersion", "metadata", "page", "contents", "modules"],
        )

    def test_optional_fields_are_omitted_when_absent(self) -> None:
        value = document().to_dict()
        self.assertEqual(list(value["metadata"]), ["title"])
        self.assertNotIn("caption", value["contents"][0])

    def test_integer_valued_floats_are_written_without_a_decimal_point(self) -> None:
        built = document(
            page=Page(paper="a4", orientation="portrait", margin=margin(2.0))
        )
        value = built.to_dict()
        self.assertEqual(value["page"]["margin"]["top"]["value"], 2)
        self.assertIn('"value": 2,', built.to_json())

    def test_non_integer_floats_keep_their_shortest_form(self) -> None:
        value = document(
            page=Page(paper="a4", orientation="portrait", margin=margin(2.5))
        ).to_dict()
        self.assertEqual(value["page"]["margin"]["top"]["value"], 2.5)

    def test_a_large_number_is_written_in_the_number_domain_of_the_contract(
        self,
    ) -> None:
        built = document(
            page=Page(
                paper="a4",
                orientation="portrait",
                margin=margin(9007199254740992),
            )
        )
        self.assertIn('"value": 9007199254740992,', built.to_json())

    def test_unicode_is_preserved(self) -> None:
        text = document(metadata=Metadata(title="보고서")).to_json()
        self.assertIn("보고서", text)
        self.assertNotIn("\\u", text)

    def test_a_lone_surrogate_is_rejected(self) -> None:
        built = document(metadata=Metadata(title="Title\uD800"))
        with self.assertRaises(SerializationError) as caught:
            built.to_json()
        self.assertEqual(
            caught.exception.diagnostics[0].code,
            "TYPCAST-IR-0003",
        )

    def test_a_lone_trailing_surrogate_is_rejected(self) -> None:
        built = document(metadata=Metadata(title="Title\uDC00"))
        with self.assertRaises(SerializationError) as caught:
            built.to_json()
        self.assertEqual(
            caught.exception.diagnostics[0].code,
            "TYPCAST-IR-0003",
        )

    def test_the_output_is_valid_json(self) -> None:
        value = json.loads(document().to_json())
        self.assertEqual(value["schemaVersion"], "1.0.0")

    def test_every_node_type_is_serialized(self) -> None:
        built = document(
            contents=[
                Heading(level=1, content=[Text("Heading")]),
                Paragraph(
                    content=[
                        Text("Text"),
                        Bold(content=[Text("Bold")]),
                        Italic(content=[Text("Italic")]),
                        Monospace(content=[Text("Monospace")]),
                        Link(href="https://example.com", content=[Text("Link")]),
                        LineBreak(),
                        RawSpan(format="math", value="x^2"),
                    ]
                ),
                ListBlock(ordered=True, items=[[Text("Item")]]),
                Table(
                    columns=[TableColumn(header=[Text("Header")], align="left")],
                    rows=[[[Text("Cell")]]],
                ),
                Image(path="figures/logo.png", alt="Logo"),
                PageBreak(),
                RawBlock(format="markup", value="#text()"),
            ],
            modules=[Module(path="modules/report.typ", alias="report")],
        )
        value = built.to_dict()
        types = [block["type"] for block in value["contents"]]
        self.assertEqual(
            types,
            [
                "heading",
                "paragraph",
                "list",
                "table",
                "image",
                "pageBreak",
                "raw",
            ],
        )
        span_types = [span["type"] for span in value["contents"][1]["content"]]
        self.assertEqual(
            span_types,
            ["text", "bold", "italic", "monospace", "link", "lineBreak", "raw"],
        )


class DeserializationTests(unittest.TestCase):
    """Checks the reader of the document IR."""

    def test_malformed_json_is_rejected(self) -> None:
        with self.assertRaises(SerializationError) as caught:
            Document.from_json("{")
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0001")

    def test_a_non_object_root_is_rejected(self) -> None:
        with self.assertRaises(SerializationError) as caught:
            Document.from_json("[]")
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0004")

    def test_an_unknown_root_field_is_rejected(self) -> None:
        value = document().to_dict()
        value["theme"] = "dark"
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-VAL-0002")

    def test_a_missing_required_field_is_rejected(self) -> None:
        value = document().to_dict()
        del value["metadata"]
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-VAL-0001")

    def test_an_unknown_node_field_is_rejected(self) -> None:
        value = document().to_dict()
        value["contents"][0]["style"] = "lead"
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-VAL-0002")

    def test_an_unknown_discriminator_is_rejected(self) -> None:
        value = document().to_dict()
        value["contents"][0]["type"] = "quote"
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-VAL-0003")

    def test_an_inherited_key_is_not_a_discriminator(self) -> None:
        value = document().to_dict()
        value["contents"][0]["type"] = "constructor"
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-VAL-0003")

    def test_an_unsupported_version_is_rejected(self) -> None:
        value = document().to_dict()
        value["schemaVersion"] = "2.0.0"
        with self.assertRaises(SerializationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0002")

    def test_a_version_with_unicode_digits_is_rejected(self) -> None:
        value = document().to_dict()
        value["schemaVersion"] = "\u0661.0.0"
        with self.assertRaises(SerializationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0002")

    def test_a_version_with_a_trailing_newline_is_rejected(self) -> None:
        value = document().to_dict()
        value["schemaVersion"] = "1.0.0\n"
        with self.assertRaises(SerializationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0002")

    def test_an_integer_valued_float_level_is_accepted(self) -> None:
        value = document().to_dict()
        value["contents"] = [
            {"type": "heading", "level": 1.0, "content": [{"type": "text", "value": "H"}]}
        ]
        parsed = Document.from_dict(value)
        self.assertEqual(parsed.contents[0].level, 1)

    def test_a_number_that_overflows_the_number_domain_is_rejected(self) -> None:
        value = document().to_dict()
        value["page"]["margin"]["top"]["value"] = 10**400
        with self.assertRaises(SerializationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].code, "TYPCAST-IR-0004")

    def test_a_supported_patch_version_is_accepted(self) -> None:
        value = document().to_dict()
        value["schemaVersion"] = "1.0.7"
        parsed = Document.from_dict(value)
        self.assertEqual(parsed.schema_version, "1.0.7")

    def test_a_missing_modules_field_defaults_to_an_empty_list(self) -> None:
        value = document().to_dict()
        del value["modules"]
        parsed = Document.from_dict(value)
        self.assertEqual(parsed.modules, ())

    def test_the_diagnostic_path_points_at_the_failing_node(self) -> None:
        value = document().to_dict()
        value["contents"][0]["style"] = "lead"
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].path, "/contents/0/style")

    def test_the_path_of_a_nested_value_is_not_prefixed_twice(self) -> None:
        value = document().to_dict()
        value["page"]["margin"]["top"]["value"] = -1
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(
            caught.exception.diagnostics[0].path,
            "/page/margin/top/value",
        )

    def test_the_path_of_a_nested_optional_value_is_not_prefixed_twice(self) -> None:
        value = document().to_dict()
        value["contents"] = [
            {
                "type": "image",
                "path": "figure.png",
                "alt": "Figure",
                "width": {"value": -2, "unit": "cm"},
            }
        ]
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(
            caught.exception.diagnostics[0].path,
            "/contents/0/width/value",
        )

    def test_an_unknown_field_is_reported_with_an_escaped_pointer(self) -> None:
        value = document().to_dict()
        value["bad/name"] = 1
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].path, "/bad~1name")

    def test_an_unknown_field_with_a_tilde_is_escaped(self) -> None:
        value = document().to_dict()
        value["a~b"] = 1
        with self.assertRaises(ValidationError) as caught:
            Document.from_dict(value)
        self.assertEqual(caught.exception.diagnostics[0].path, "/a~0b")

    def test_every_error_carries_a_diagnostic(self) -> None:
        with self.assertRaises(TypcastError) as caught:
            Document.from_json("{")
        self.assertTrue(caught.exception.diagnostics)
        self.assertEqual(caught.exception.diagnostics[0].severity, "error")
        self.assertEqual(caught.exception.diagnostics[0].phase, "serialization")


class RoundTripTests(unittest.TestCase):
    """Checks that the reader and the writer preserve the document."""

    def test_the_round_trip_is_stable(self) -> None:
        text = document().to_json()
        self.assertEqual(Document.from_json(text).to_json(), text)

    def test_the_round_trip_keeps_the_model(self) -> None:
        built = document(
            metadata=Metadata(title="Title", author="Author", date="2026-11-24"),
            modules=[Module(path="modules/report.typ", items=["currency"])],
        )
        parsed = Document.from_json(built.to_json())
        self.assertEqual(parsed.to_dict(), built.to_dict())
        self.assertEqual(parsed.metadata.author, "Author")
        self.assertEqual(parsed.modules[0].items, ("currency",))


if __name__ == "__main__":
    unittest.main()
