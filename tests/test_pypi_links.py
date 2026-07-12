"""Tests for the PyPI long-description link rewriter and version helpers (D-PyPI).

The rewriter is a pure function; the PyPI lookup is tested with a mocked urllib so the suite
never touches the network.
"""

from __future__ import annotations

import unittest
from unittest import mock

from agent_workflows.pypi_links import (
    owner_repo_from_url,
    rewrite_relative_links,
)
from agent_workflows import versioning


class RewriteTests(unittest.TestCase):
    def rw(self, md):
        return rewrite_relative_links(md, "fariello", "agent-workflows", "v1.1.0")

    def test_relative_doc_link_to_blob(self):
        out = self.rw("[CLI](docs/cli.md)")
        self.assertEqual(
            out,
            "[CLI](https://github.com/fariello/agent-workflows/blob/v1.1.0/docs/cli.md)",
        )

    def test_relative_image_to_raw(self):
        out = self.rw("![d](img/arch.png)")
        self.assertIn("/raw/v1.1.0/img/arch.png", out)
        self.assertTrue(out.startswith("!["))

    def test_bang_syntax_forces_raw_even_without_ext(self):
        out = self.rw("![x](assets/logo)")
        self.assertIn("/raw/v1.1.0/assets/logo", out)

    def test_leading_dot_slash_normalized(self):
        out = self.rw("[x](./a/b.md)")
        self.assertIn("/blob/v1.1.0/a/b.md", out)

    def test_fragment_preserved_on_doc(self):
        out = self.rw("[x](specs/f.md#usage)")
        self.assertIn("/blob/v1.1.0/specs/f.md#usage", out)

    def test_absolute_and_anchor_and_mailto_untouched(self):
        for link in (
            "[a](https://x.com)",
            "[b](#sec)",
            "[c](mailto:a@b.co)",
            "[d](//cdn/x)",
        ):
            self.assertEqual(self.rw(link), link)

    def test_parent_escape_left_alone(self):
        link = "[x](../outside/thing.md)"
        self.assertEqual(self.rw(link), link)

    def test_deterministic(self):
        md = "[a](docs/a.md) ![b](img/b.png) [ext](https://x.com)"
        self.assertEqual(self.rw(md), self.rw(md))


class OwnerRepoTests(unittest.TestCase):
    def test_github_url_variants(self):
        self.assertEqual(
            owner_repo_from_url("https://github.com/fariello/agent-workflows"),
            ("fariello", "agent-workflows"),
        )
        self.assertEqual(owner_repo_from_url("https://github.com/o/r.git/"), ("o", "r"))

    def test_non_github_is_none(self):
        self.assertIsNone(owner_repo_from_url("https://gitlab.com/o/r"))
        self.assertIsNone(owner_repo_from_url("not a url"))


class PyPIVersionTests(unittest.TestCase):
    def test_next_version_ok(self):
        self.assertTrue(versioning.next_version_ok("1.2.0", "1.1.0"))
        self.assertTrue(
            versioning.next_version_ok("1.1.0", "1.1.0")
        )  # equal is allowed
        self.assertFalse(versioning.next_version_ok("1.0.0", "1.1.0"))
        self.assertTrue(versioning.next_version_ok("0.1.0", None))  # unpublished

    def test_latest_pypi_version_success(self):
        payload = b'{"info": {"version": "2.3.4"}}'
        cm = mock.MagicMock()
        cm.read.return_value = payload
        cm.__enter__.return_value = cm
        with mock.patch("urllib.request.urlopen", return_value=cm):
            self.assertEqual(versioning.latest_pypi_version("whatever"), "2.3.4")

    def test_latest_pypi_version_failure_is_none(self):
        import urllib.error

        with mock.patch(
            "urllib.request.urlopen", side_effect=urllib.error.URLError("offline")
        ):
            self.assertIsNone(versioning.latest_pypi_version("whatever"))

    def test_latest_pypi_version_non_dict_json_returns_none(self):
        # TEST-03: latest_pypi_version returns None when JSON payload is a list
        payload = b'["not", "a", "dict"]'
        cm = mock.MagicMock()
        cm.read.return_value = payload
        cm.__enter__.return_value = cm
        with mock.patch("urllib.request.urlopen", return_value=cm):
            self.assertIsNone(versioning.latest_pypi_version("whatever"))


if __name__ == "__main__":
    unittest.main()
