import functools
import http.server
import tempfile
import threading
import unittest
from pathlib import Path

from check_links import check_links, check_url


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """A request handler that does not write to the test log."""

    def log_message(self, format: str, *args: object) -> None:
        return


class LinkCheckTests(unittest.TestCase):
    """Checks the external link check of the documents."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        (self.root / "docs").mkdir()
        (self.root / "README.md").write_text(
            "# Readme\n\nA [link](https://example.invalid/page).\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_readme(self, text: str) -> None:
        (self.root / "README.md").write_text(text, encoding="utf-8")

    def test_an_unreachable_link_is_reported(self) -> None:
        problems = check_links(str(self.root), timeout=5.0)

        self.assertEqual(len(problems), 1)
        self.assertIn("example.invalid", problems[0][0])

    def test_a_versioned_raw_url_is_skipped(self) -> None:
        self.write_readme(
            "# Readme\n\n"
            "A [schema](https://raw.githubusercontent.com/zuudevs/typcast/"
            "v1.0.0/specs/schemas/validator.schema.json).\n"
        )

        problems = check_links(str(self.root), timeout=5.0)

        self.assertEqual(problems, [])

    def test_a_resolved_link_is_not_reported(self) -> None:
        handler = functools.partial(QuietHandler, directory=str(self.root))
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/README.md"
            self.write_readme(f"# Readme\n\nA [link]({url}).\n")

            problems = check_links(str(self.root), timeout=5.0)

            self.assertEqual(problems, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    def test_a_missing_file_is_reported_by_the_url_check(self) -> None:
        problem = check_url("http://127.0.0.1:1/missing", timeout=5.0)

        self.assertIsNotNone(problem)


if __name__ == "__main__":
    unittest.main()
