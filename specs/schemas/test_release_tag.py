"""Unit tests of the release tag validation of the schema contract.

Every published schema carries the identity of a release tag, so the contract
and the publisher must agree on what a release tag is. The tests use the same
call as the contract check, so a pattern that matches only the prefix of a tag
fails them.
"""

import unittest

from schema_tests import RELEASE_TAG_PATTERN


class ReleaseTagTests(unittest.TestCase):
    """Checks that the release tag pattern matches the whole tag."""

    def assert_valid(self, tag: str) -> None:
        """Asserts that a tag is a release tag."""
        with self.subTest(tag=tag):
            self.assertIsNotNone(RELEASE_TAG_PATTERN.match(tag))

    def assert_invalid(self, tag: str) -> None:
        """Asserts that a tag is not a release tag."""
        with self.subTest(tag=tag):
            self.assertIsNone(RELEASE_TAG_PATTERN.match(tag))

    def test_a_release_tag_is_valid(self) -> None:
        for tag in ("v1.0.0", "v0.1.0", "v12.34.56"):
            self.assert_valid(tag)

    def test_a_tag_with_a_suffix_is_invalid(self) -> None:
        for tag in ("v1.0.0-invalid", "v1.0.0garbage", "v1.0.0anything"):
            self.assert_invalid(tag)

    def test_a_tag_without_the_prefix_is_invalid(self) -> None:
        for tag in ("1.0.0", "main", "v", ""):
            self.assert_invalid(tag)

    def test_a_partial_tag_is_invalid(self) -> None:
        for tag in ("v1.0", "v1", "v1.0.0.0"):
            self.assert_invalid(tag)


if __name__ == "__main__":
    unittest.main()
