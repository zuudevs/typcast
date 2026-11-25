"""Check the external links of the documents.

The check uses the network, so it belongs to the continuous integration lane
and not to the repository gate. An unreachable link is a warning, never a
blocking failure, because an outage of an external site must not block an
unrelated change (`DOC-010`).

The versioned raw URLs of the schemas are skipped. They resolve only after the
first release tag exists, and the release lane verifies them against the
tagged commit with `publish_schemas verify`.

Usage:

    python scripts/check_links.py [--root PATH] [--timeout SECONDS]
"""

from __future__ import annotations

import argparse
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from validate_docs import (
    RAW_URL_RE,
    Report,
    checked_files,
    external_links,
    find_root,
)

USER_AGENT = "typcast-docs-links"
DEFAULT_TIMEOUT = 10.0


def check_url(url: str, timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """Returns the problem of one URL, or None when the URL resolves.

    A server that refuses a HEAD request is asked for the document itself,
    because some servers only answer one of the two methods.
    """
    for method in ("HEAD", "GET"):
        request = Request(url, method=method, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=timeout) as response:
                status = response.status
        except HTTPError as error:
            if method == "HEAD" and error.code in (403, 405, 501):
                continue
            return f"the server answered {error.code}"
        except (URLError, OSError) as error:
            return f"the URL cannot be reached: {error.reason}"
        if status >= 400:
            return f"the server answered {status}"
        return None
    return "the server refused the request"


def check_links(
    root: str,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[tuple[str, str, str]]:
    """Returns the unreachable links: the URL, its file, and the problem."""
    repository = find_root(root)
    report = Report()
    problems: list[tuple[str, str, str]] = []
    for url, rel in external_links(repository, checked_files(repository)):
        if RAW_URL_RE.match(url):
            continue
        problem = check_url(url, timeout)
        if problem:
            problems.append((url, rel, problem))
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=None, help="repository root")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help="timeout of one request, in seconds",
    )
    args = parser.parse_args(argv)

    problems = check_links(args.root, args.timeout)
    for url, rel, problem in problems:
        print(f"WARN {rel}: {url}: {problem}", file=sys.stderr)
    print(f"unreachable links: {len(problems)}")
    print("the check reports warnings only; it never blocks a merge")
    return 0


if __name__ == "__main__":
    sys.exit(main())
