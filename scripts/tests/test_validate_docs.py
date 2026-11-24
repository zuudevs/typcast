import tempfile
import unittest
from pathlib import Path

from validate_docs import (
    Report,
    check_codeowners,
    check_markdown_lint,
    check_mermaid,
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
        path.write_text(text, encoding="utf-8")
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


if __name__ == "__main__":
    unittest.main()
