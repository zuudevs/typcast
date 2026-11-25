import tempfile
import unittest
from pathlib import Path

from validate_docs import (
    Report,
    check_codeowners,
    check_encoding,
    check_markdown_lint,
    check_mermaid,
    check_schema_references,
)


class GateTestCase(unittest.TestCase):
    """Base class that writes documents into a temporary directory."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def report_for(self, path: Path) -> Report:
        report = Report()
        check_markdown_lint(self.root, [path], report)
        check_mermaid(self.root, [path], report)
        return report


class MarkdownLintTests(GateTestCase):
    def test_a_clean_document_reports_no_error(self) -> None:
        path = self.write(
            "clean.md",
            "# Title\n"
            "\n"
            "## Section\n"
            "\n"
            "Text with a [link](other.md).\n"
            "\n"
            "### Sub section\n"
            "\n"
            "```python\n"
            "print(1)\n"
            "```\n"
            "\n"
            "| Name | Value |\n"
            "|---|---|\n"
            "| a | 1 |\n",
        )

        report = self.report_for(path)

        self.assertEqual(report.errors, [])

    def test_a_skipped_heading_level_is_reported(self) -> None:
        path = self.write(
            "levels.md",
            "# Title\n"
            "\n"
            "#### Too deep\n"
            "\n"
            "Text.\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("skips level" in error for error in report.errors),
            report.errors,
        )

    def test_a_heading_without_blank_lines_is_reported(self) -> None:
        path = self.write(
            "blank.md",
            "# Title\n"
            "## Section\n"
            "\n"
            "Text.\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("blank line" in error for error in report.errors),
            report.errors,
        )

    def test_two_blank_lines_in_a_row_are_reported(self) -> None:
        path = self.write(
            "gap.md",
            "# Title\n"
            "\n"
            "\n"
            "Text.\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("more than one blank line" in error for error in report.errors),
            report.errors,
        )

    def test_a_table_row_with_a_missing_column_is_reported(self) -> None:
        path = self.write(
            "table.md",
            "# Title\n"
            "\n"
            "| Name | Value |\n"
            "|---|---|\n"
            "| a |\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("table row" in error for error in report.errors),
            report.errors,
        )

    def test_a_document_that_does_not_start_with_a_title_is_reported(self) -> None:
        path = self.write(
            "intro.md",
            "Text first.\n"
            "\n"
            "# Title\n"
            "\n"
            "Text.\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("level-1 heading" in error for error in report.errors),
            report.errors,
        )


class MermaidTests(GateTestCase):
    def test_a_valid_flowchart_reports_no_error(self) -> None:
        path = self.write(
            "flow.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  A["First"] --> B["Second"]\n'
            '  B --> C{"Third?"}\n'
            '  C -- Yes --> D["Fourth"]\n'
            '  C -- No --> E["Fifth"]\n'
            '  D -. "no dependency" .-> F["Sixth"]\n'
            "```\n",
        )

        report = self.report_for(path)

        self.assertEqual(report.errors, [])

    def test_a_flowchart_without_a_direction_is_reported(self) -> None:
        path = self.write(
            "direction.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "flowchart\n"
            '  A["First"] --> B["Second"]\n'
            "```\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("needs a direction" in error for error in report.errors),
            report.errors,
        )

    def test_a_flowchart_statement_without_a_target_is_reported(self) -> None:
        path = self.write(
            "target.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  A["First"] -->\n'
            "```\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any(
                "cannot be read" in error or "edge between" in error
                for error in report.errors
            ),
            report.errors,
        )

    def test_an_unreadable_node_is_reported(self) -> None:
        path = self.write(
            "node.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "flowchart LR\n"
            '  A["First"] --> B["unbalanced\n'
            "```\n",
        )

        report = self.report_for(path)

        self.assertTrue(report.errors, report.errors)

    def test_a_valid_sequence_diagram_reports_no_error(self) -> None:
        path = self.write(
            "sequence.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "  participant U as User\n"
            "  participant S as Service\n"
            "  U->>S: request\n"
            "  S-->>U: response\n"
            "  loop every minute\n"
            "    S->>S: tick\n"
            "  end\n"
            "```\n",
        )

        report = self.report_for(path)

        self.assertEqual(report.errors, [])

    def test_an_undeclared_participant_is_reported(self) -> None:
        path = self.write(
            "participant.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "  U->>S: request\n"
            "```\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("not declared" in error for error in report.errors),
            report.errors,
        )

    def test_an_unclosed_block_is_reported(self) -> None:
        path = self.write(
            "block.md",
            "# Title\n"
            "\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "  participant U as User\n"
            "  loop every minute\n"
            "    U->>U: tick\n"
            "```\n",
        )

        report = self.report_for(path)

        self.assertTrue(
            any("not closed" in error for error in report.errors),
            report.errors,
        )


class CodeOwnersTests(GateTestCase):
    def check(self) -> Report:
        report = Report()
        check_codeowners(self.root, report)
        return report

    def test_a_valid_file_reports_no_error(self) -> None:
        self.write(".github/CODEOWNERS", "# Owners\n\n* @zuudevs\n")

        report = self.check()

        self.assertEqual(report.errors, [])

    def test_a_missing_file_is_reported(self) -> None:
        report = self.check()

        self.assertTrue(
            any("missing" in error for error in report.errors),
            report.errors,
        )

    def test_a_rule_without_an_owner_is_reported(self) -> None:
        self.write(".github/CODEOWNERS", "*\n")

        report = self.check()

        self.assertTrue(report.errors, report.errors)

    def test_an_owner_without_an_at_sign_is_reported(self) -> None:
        self.write(".github/CODEOWNERS", "* zuudevs\n")

        report = self.check()

        self.assertTrue(
            any("does not start with @" in error for error in report.errors),
            report.errors,
        )

    def test_a_file_without_a_rule_for_every_path_is_reported(self) -> None:
        self.write(".github/CODEOWNERS", "docs/ @zuudevs\n")

        report = self.check()

        self.assertTrue(
            any("covers every path" in error for error in report.errors),
            report.errors,
        )


class EncodingTests(GateTestCase):
    """Checks the encoding and the text hygiene rules of the gate."""

    def write_bytes(self, name: str, data: bytes) -> Path:
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def report_for(self, path: Path) -> Report:
        report = Report()
        check_encoding(self.root, [path], report)
        return report

    def test_a_clean_file_reports_no_error(self) -> None:
        path = self.write("clean.txt", "Text with UTF-8: Ä.\n")

        report = self.report_for(path)

        self.assertEqual(report.errors, [])

    def test_a_byte_order_mark_is_reported(self) -> None:
        path = self.write_bytes("bom.txt", b"\xef\xbb\xbfText.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("byte order mark" in error for error in report.errors),
            report.errors,
        )

    def test_invalid_utf8_is_reported(self) -> None:
        path = self.write_bytes("invalid.txt", b"Text \xff.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("invalid UTF-8" in error for error in report.errors),
            report.errors,
        )

    def test_crlf_line_endings_are_reported(self) -> None:
        path = self.write_bytes("crlf.txt", b"First.\r\nSecond.\r\n")

        report = self.report_for(path)

        self.assertTrue(
            any("CRLF" in error for error in report.errors),
            report.errors,
        )

    def test_a_missing_final_newline_is_reported(self) -> None:
        path = self.write("final.txt", "Text without a final newline.")

        report = self.report_for(path)

        self.assertTrue(
            any("final newline" in error for error in report.errors),
            report.errors,
        )

    def test_a_replacement_character_is_reported(self) -> None:
        path = self.write("replacement.txt", "Text with \ufffd.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("replacement character" in error for error in report.errors),
            report.errors,
        )

    def test_a_mojibake_sequence_is_reported(self) -> None:
        path = self.write("mojibake.txt", "Text with \u00c3\u00a4.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("mojibake" in error for error in report.errors),
            report.errors,
        )

    def test_an_emoji_is_reported(self) -> None:
        path = self.write("emoji.txt", "Text with \U0001f600.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("emoji or dingbat" in error for error in report.errors),
            report.errors,
        )

    def test_trailing_whitespace_is_reported(self) -> None:
        path = self.write("trailing.txt", "Text with trailing space. \n")

        report = self.report_for(path)

        self.assertTrue(
            any("trailing whitespace" in error for error in report.errors),
            report.errors,
        )

    def test_a_tab_character_is_reported(self) -> None:
        path = self.write("tab.txt", "Text with\ta tab.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("tab character" in error for error in report.errors),
            report.errors,
        )

    def test_a_placeholder_marker_is_reported(self) -> None:
        path = self.write("placeholder.md", "# Title\n\nTODO: write this.\n")

        report = self.report_for(path)

        self.assertTrue(
            any("placeholder marker" in error for error in report.errors),
            report.errors,
        )


class SchemaReferenceTests(GateTestCase):
    """Checks the release tag rule of the raw URL references."""

    def setUp(self) -> None:
        super().setUp()
        self.write("specs/schemas/validator.schema.json", "{}\n")

    def report_for(self, path: Path) -> Report:
        report = Report()
        check_schema_references(self.root, [path], report)
        return report

    def write_reference(self, name: str, version: str) -> Path:
        return self.write(
            name,
            "# Title\n"
            "\n"
            f"https://raw.githubusercontent.com/zuudevs/typcast/{version}/"
            "specs/schemas/validator.schema.json\n",
        )

    def test_a_release_tag_reports_no_error(self) -> None:
        path = self.write_reference("reference.md", "v1.0.0")

        report = self.report_for(path)

        self.assertEqual(report.errors, [])

    def test_a_release_tag_with_a_suffix_is_reported(self) -> None:
        path = self.write_reference("suffix.md", "v1.0.0-invalid")

        report = self.report_for(path)

        self.assertTrue(
            any("is not a release tag" in error for error in report.errors),
            report.errors,
        )

    def test_a_partial_release_tag_is_reported(self) -> None:
        path = self.write_reference("partial.md", "v1.0")

        report = self.report_for(path)

        self.assertTrue(
            any("is not a release tag" in error for error in report.errors),
            report.errors,
        )


if __name__ == "__main__":
    unittest.main()
