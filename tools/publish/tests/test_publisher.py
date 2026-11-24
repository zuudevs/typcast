import functools
import http.server
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path, PurePosixPath

from typcast_publish.errors import PublishError
from typcast_publish.publisher import (
    check_published_bundle,
    publish_bundle,
    published_url,
    read_manifest,
    verify_published_urls,
    write_manifest,
)

# The node schema does not exist yet. It is the tracked defect SCH-D01.
KNOWN_MISSING_REFERENCE = "definitions/node.schema.json"


def runfiles_candidates() -> list[Path]:
    candidates: list[Path] = []
    runfiles = os.environ.get("RUNFILES_DIR")
    workspace = os.environ.get("TEST_WORKSPACE")
    if runfiles:
        base = Path(runfiles)
        candidates.append(base)
        if workspace:
            candidates.append(base / workspace)
        candidates.append(base / "_main")
    cwd = Path.cwd()
    candidates.append(cwd)
    if workspace:
        candidates.append(cwd / workspace)
    candidates.extend(Path(__file__).resolve().parents)
    return candidates


def repository_candidates() -> list[Path]:
    """Returns the repository root, so that a local build output is found."""
    candidates: list[Path] = []
    for candidate in runfiles_candidates():
        candidates.append(candidate)
        candidates.append(candidate / "bazel-bin")
    return candidates


def find_built_bundle() -> Path | None:
    """Locates the built schema bundle in a Bazel runfiles tree."""
    candidates = runfiles_candidates() + repository_candidates()
    for candidate in candidates:
        bundle = candidate / "specs" / "schemas"
        if (bundle / "api" / "types" / "alignment.schema.json").exists():
            return bundle
    return None


def find_manifest() -> Path | None:
    """Locates the bundle manifest in a Bazel runfiles tree."""
    candidates = runfiles_candidates() + repository_candidates()
    for candidate in candidates:
        manifest = candidate / "specs" / "schemas" / "schema_manifest.txt"
        if manifest.is_file():
            return manifest
    return None


def collect_references(document: object) -> list[str]:
    references: list[str] = []
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "$ref" and isinstance(value, str):
                references.append(value)
            else:
                references.extend(collect_references(value))
    elif isinstance(document, list):
        for value in document:
            references.extend(collect_references(value))
    return references


class PublishBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.bundle = self.root / "bundle"
        self.bundle.mkdir()
        (self.bundle / "validator.schema.json").write_text(
            json.dumps(
                {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "$id": "https://typcast.local/schemas/validation.schema.json",
                    "type": "object",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.manifest = ["validator.schema.json"]

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def publish(self, output: Path, version: str = "v1.0.0") -> list[str]:
        return publish_bundle(self.bundle, self.manifest, output, version)

    def test_publish_sets_the_published_identity(self) -> None:
        output = self.root / "published"

        self.publish(output)

        document = json.loads(
            (output / "validator.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            document["$id"],
            "https://raw.githubusercontent.com/zuudevs/typcast/v1.0.0/"
            "specs/schemas/validator.schema.json",
        )
        self.assertEqual(
            document["$schema"],
            "https://json-schema.org/draft/2020-12/schema",
        )
        self.assertEqual(document["type"], "object")

    def test_publish_keeps_the_schema_dialect_first(self) -> None:
        output = self.root / "published"

        self.publish(output)

        text = (output / "validator.schema.json").read_text(encoding="utf-8")
        self.assertLess(text.index('"$schema"'), text.index('"$id"'))

    def test_publish_preserves_the_relative_paths(self) -> None:
        nested = self.bundle / "api" / "types"
        nested.mkdir(parents=True)
        (nested / "paper.schema.json").write_text(
            json.dumps({"type": "object"}, indent=2) + "\n",
            encoding="utf-8",
        )
        self.manifest = ["api/types/paper.schema.json", "validator.schema.json"]
        output = self.root / "published"

        published = self.publish(output)

        self.assertEqual(
            published,
            ["api/types/paper.schema.json", "validator.schema.json"],
        )
        self.assertTrue((output / "api" / "types" / "paper.schema.json").is_file())

    def test_publish_ignores_files_outside_the_manifest(self) -> None:
        (self.bundle / "stale.schema.json").write_text("{}\n", encoding="utf-8")
        output = self.root / "published"

        published = self.publish(output)

        self.assertEqual(published, ["validator.schema.json"])
        self.assertFalse((output / "stale.schema.json").exists())

    def test_publish_writes_utf8_without_a_byte_order_mark(self) -> None:
        (self.bundle / "validator.schema.json").write_text(
            json.dumps({"title": "café"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        output = self.root / "published"

        self.publish(output)

        data = (output / "validator.schema.json").read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertIn("café", data.decode("utf-8"))
        self.assertTrue(data.endswith(b"\n"))

    def test_publish_rejects_a_development_version(self) -> None:
        with self.assertRaises(PublishError):
            publish_bundle(
                self.bundle,
                self.manifest,
                self.root / "published",
                "main",
            )

    def test_publish_rejects_a_version_without_a_tag_prefix(self) -> None:
        with self.assertRaises(PublishError):
            publish_bundle(
                self.bundle,
                self.manifest,
                self.root / "published",
                "1.0.0",
            )

    def test_publish_rejects_a_partial_version(self) -> None:
        with self.assertRaises(PublishError):
            publish_bundle(
                self.bundle,
                self.manifest,
                self.root / "published",
                "v1.0",
            )

    def test_publish_rejects_a_missing_bundle(self) -> None:
        with self.assertRaises(PublishError):
            publish_bundle(
                self.root / "missing",
                self.manifest,
                self.root / "published",
                "v1.0.0",
            )

    def test_publish_rejects_an_incomplete_bundle(self) -> None:
        with self.assertRaises(PublishError):
            publish_bundle(
                self.bundle,
                ["missing.schema.json"],
                self.root / "published",
                "v1.0.0",
            )

    def test_check_accepts_a_published_bundle(self) -> None:
        output = self.root / "published"
        self.publish(output)

        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            output,
            "v1.0.0",
        )

        self.assertEqual(problems, [])

    def test_check_reports_a_missing_file(self) -> None:
        output = self.root / "published"
        self.publish(output)
        (output / "validator.schema.json").unlink()

        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            output,
            "v1.0.0",
        )

        self.assertEqual(
            problems,
            ["missing published file: validator.schema.json"],
        )

    def test_check_reports_a_different_file(self) -> None:
        output = self.root / "published"
        self.publish(output)
        (output / "validator.schema.json").write_text("{}\n", encoding="utf-8")

        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            output,
            "v1.0.0",
        )

        self.assertEqual(
            problems,
            ["published file differs from the build: validator.schema.json"],
        )

    def test_check_reports_an_unexpected_file(self) -> None:
        output = self.root / "published"
        self.publish(output)
        (output / "extra.schema.json").write_text("{}\n", encoding="utf-8")

        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            output,
            "v1.0.0",
        )

        self.assertEqual(
            problems,
            ["unexpected published file: extra.schema.json"],
        )

    def test_check_reports_a_missing_published_directory(self) -> None:
        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            self.root / "missing",
            "v1.0.0",
        )

        self.assertEqual(len(problems), 1)
        self.assertIn("published bundle not found", problems[0])


class ManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_manifest_round_trip(self) -> None:
        manifest = self.root / "manifest.txt"

        write_manifest(["b.schema.json", "a.schema.json"], manifest)

        self.assertEqual(
            read_manifest(manifest),
            ["a.schema.json", "b.schema.json"],
        )

    def test_manifest_is_written_without_a_byte_order_mark(self) -> None:
        manifest = self.root / "manifest.txt"

        write_manifest(["a.schema.json"], manifest)

        data = manifest.read_bytes()
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertTrue(data.endswith(b"\n"))

    def test_empty_manifest_is_rejected(self) -> None:
        with self.assertRaises(PublishError):
            write_manifest([], self.root / "manifest.txt")

    def test_missing_manifest_is_rejected(self) -> None:
        with self.assertRaises(PublishError):
            read_manifest(self.root / "missing.txt")


class PublishedBundleTests(unittest.TestCase):
    """Checks the built bundle that the repository publishes."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.bundle = find_built_bundle()
        self.manifest_path = find_manifest()
        if self.bundle is None or self.manifest_path is None:
            if os.environ.get("RUNFILES_DIR"):
                self.fail("the built schema bundle was not found")
            self.skipTest("the built schema bundle requires a Bazel build")
        self.manifest = read_manifest(self.manifest_path)
        self.published = self.root / "published"

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def publish(self, version: str = "v1.0.0") -> list[str]:
        return publish_bundle(self.bundle, self.manifest, self.published, version)

    def test_the_manifest_names_every_bundle_file(self) -> None:
        self.assertIn("validator.schema.json", self.manifest)
        self.assertIn("api/types/alignment.schema.json", self.manifest)
        self.assertIn("api/types/length.schema.json", self.manifest)
        self.assertIn("api/types/paper.schema.json", self.manifest)
        self.assertIn("definitions/bound.schema.json", self.manifest)

    def test_every_published_file_has_the_release_identity(self) -> None:
        published = self.publish()

        self.assertTrue(published)
        for relative_path in published:
            document = json.loads(
                (self.published / relative_path).read_text(encoding="utf-8")
            )
            self.assertEqual(
                document["$id"],
                published_url("v1.0.0", relative_path),
            )

    def test_every_relative_reference_resolves(self) -> None:
        self.publish()

        for path in sorted(self.published.rglob("*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            for reference in collect_references(document):
                if reference.startswith(("http://", "https://", "#")):
                    continue
                target = (path.parent / reference).resolve()
                if not target.exists():
                    normalized = PurePosixPath(reference).as_posix()
                    self.assertEqual(
                        normalized,
                        KNOWN_MISSING_REFERENCE,
                        f"{path.name} references {reference}",
                    )

    def test_the_published_bundle_matches_the_build(self) -> None:
        self.publish()

        problems = check_published_bundle(
            self.bundle,
            self.manifest,
            self.published,
            "v1.0.0",
        )

        self.assertEqual(problems, [])


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    """A request handler that does not write to the test log."""

    def log_message(self, format: str, *args: object) -> None:
        return


class PublishedUrlTests(unittest.TestCase):
    """Checks that the published URLs serve the committed files."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.published = self.root / "published"
        self.published.mkdir()
        self.served = self.root / "served" / "v1.0.0" / "specs" / "schemas"
        self.served.mkdir(parents=True)
        (self.published / "validator.schema.json").write_text("{}\n", encoding="utf-8")
        (self.served / "validator.schema.json").write_text("{}\n", encoding="utf-8")
        self.manifest = ["validator.schema.json"]

        handler = functools.partial(QuietHandler, directory=str(self.root / "served"))
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}/"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.temporary_directory.cleanup()

    def verify(self) -> list[str]:
        return verify_published_urls(
            "v1.0.0",
            self.manifest,
            self.published,
            base_url=self.base_url,
            timeout=5.0,
        )

    def test_verify_accepts_a_resolved_url(self) -> None:
        self.assertEqual(self.verify(), [])

    def test_verify_reports_a_different_file(self) -> None:
        (self.served / "validator.schema.json").write_text("{}\n\n", encoding="utf-8")

        problems = self.verify()

        self.assertEqual(len(problems), 1)
        self.assertIn("differs from the committed file", problems[0])

    def test_verify_reports_a_missing_committed_file(self) -> None:
        (self.published / "validator.schema.json").unlink()

        problems = self.verify()

        self.assertEqual(
            problems,
            ["missing published file: validator.schema.json"],
        )

    def test_verify_reports_an_unreachable_url(self) -> None:
        self.server.shutdown()
        self.server.server_close()

        problems = self.verify()

        self.assertEqual(len(problems), 1)
        self.assertIn("cannot fetch", problems[0])

    def test_verify_rejects_a_development_version(self) -> None:
        with self.assertRaises(PublishError):
            verify_published_urls(
                "main",
                self.manifest,
                self.published,
                base_url=self.base_url,
            )


if __name__ == "__main__":
    unittest.main()
