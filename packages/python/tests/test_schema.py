"""Unit tests for the validation against the JSON Schema contract.

The tests cover the validator of the Python SDK: the keywords that the schema
contract uses, the diagnostics that the validator reports, and the relation of
the validator to the model of a document.

Usage:

    bazel test //packages/python/tests:schema_tests
"""

from __future__ import annotations

import unittest

import typcast
from typcast import (
    Document,
    Length,
    Margin,
    Metadata,
    Page,
    Paragraph,
    Text,
    validate_schema,
)
from typcast.schema import (
    ANNOTATION_KEYWORDS,
    ASSERTION_KEYWORDS,
    SCHEMAS,
    SCHEMA_ROOT,
    schema_keywords,
)


def document() -> Document:
    """Returns a document that the model accepts."""
    return Document(
        metadata=Metadata(title="Title"),
        page=Page(
            paper="a4",
            orientation="portrait",
            margin=Margin(
                top=Length(2, "cm"),
                right=Length(2, "cm"),
                bottom=Length(2, "cm"),
                left=Length(2, "cm"),
            ),
        ),
        contents=[Paragraph(content=[Text(value="Body")])],
    )


class KeywordTests(unittest.TestCase):
    """Checks the keywords that the schema contract uses."""

    def test_every_keyword_of_the_contract_is_implemented(self) -> None:
        keywords = schema_keywords()
        self.assertTrue(keywords, "the schema contract must use keywords")
        for keyword in keywords:
            with self.subTest(keyword=keyword):
                self.assertTrue(
                    keyword in ANNOTATION_KEYWORDS or keyword in ASSERTION_KEYWORDS,
                    f"the keyword '{keyword}' is not implemented by the validator",
                )

    def test_the_bundle_holds_the_schema_of_the_document(self) -> None:
        self.assertIn(SCHEMA_ROOT, SCHEMAS)
        self.assertEqual(len(SCHEMAS), 6)


class DiagnosticTests(unittest.TestCase):
    """Checks the diagnostics that the validator reports."""

    def test_an_empty_title_is_reported(self) -> None:
        value = document().to_dict()
        value["metadata"] = {"title": ""}

        diagnostics = validate_schema(value)

        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic.code, "TYPCAST-SCH-0001")
        self.assertEqual(diagnostic.phase, "validation")
        self.assertEqual(diagnostic.severity, "error")
        self.assertEqual(diagnostic.path, "/metadata/title")
        self.assertEqual(diagnostic.message, "'/metadata/title' must not be empty.")
        self.assertEqual(
            dict(diagnostic.details),
            {"keyword": "minLength", "minLength": 1},
        )

    def test_an_unknown_field_is_reported(self) -> None:
        value = document().to_dict()
        value["theme"] = "dark"

        diagnostics = validate_schema(value)

        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(diagnostic.path, "/theme")
        self.assertEqual(diagnostic.message, "'/theme' is not a known field.")
        self.assertEqual(
            dict(diagnostic.details),
            {"keyword": "additionalProperties", "field": "theme"},
        )

    def test_a_catalog_names_the_number_of_its_values(self) -> None:
        # The paper catalog holds more values than a message can list, so the
        # message names the number of the values and the details hold the list.
        value = document().to_dict()
        value["page"] = {**value["page"], "paper": "letter"}

        diagnostics = validate_schema(value)

        self.assertEqual(len(diagnostics), 1)
        diagnostic = diagnostics[0]
        self.assertEqual(
            diagnostic.message,
            "'/page/paper' must be one of the 107 allowed values, got 'letter'.",
        )
        allowed = diagnostic.details["allowed"]
        self.assertIsInstance(allowed, list)
        self.assertEqual(len(allowed), 107)

    def test_a_value_that_is_not_an_object_is_reported(self) -> None:
        diagnostics = validate_schema("Title")

        self.assertEqual(len(diagnostics), 1)
        self.assertIsNone(diagnostics[0].path)
        self.assertEqual(diagnostics[0].details["keyword"], "type")


class ModelTests(unittest.TestCase):
    """Checks the relation of the validator to the model of a document."""

    def test_a_document_that_the_model_accepts_matches_the_contract(self) -> None:
        self.assertEqual(document().validate_schema(), ())

    def test_the_json_value_of_a_document_matches_the_contract(self) -> None:
        self.assertEqual(validate_schema(document().to_dict()), ())


class SurfaceTests(unittest.TestCase):
    """Checks the public surface of the package root."""

    def test_the_package_root_exports_the_schema_api(self) -> None:
        self.assertIs(typcast.validate_schema, validate_schema)
        self.assertEqual(typcast.CODE_SCHEMA_VIOLATION, "TYPCAST-SCH-0001")
        self.assertEqual(
            typcast.CODE_SCHEMA_UNSUPPORTED_KEYWORD,
            "TYPCAST-SCH-0002",
        )

    def test_the_package_root_holds_no_contract_of_the_schema(self) -> None:
        # The contract itself lives in the schema package, so that the root
        # stays small and the contract has one place.
        for name in (
            "SCHEMAS",
            "SCHEMA_ROOT",
            "schema_keywords",
            "ANNOTATION_KEYWORDS",
            "ASSERTION_KEYWORDS",
        ):
            with self.subTest(name=name):
                self.assertFalse(hasattr(typcast, name))


if __name__ == "__main__":
    unittest.main()
