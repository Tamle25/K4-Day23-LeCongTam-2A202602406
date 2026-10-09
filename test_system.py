"""Unit tests for the Deep Research Agent system.
Tests the core functions: with_retry, slugify, and check_citations without requiring API keys or network.
Run with: python -m unittest test_system.py
"""
import unittest
from unittest.mock import MagicMock, patch

import httpx

from check_citations import check
from research import slugify
from tools import RetryableError, with_retry


class TestSlugify(unittest.TestCase):
    def test_basic_slug(self):
        self.assertEqual(slugify("survey about world model"), "survey-about-world-model")

    def test_path_traversal_prevention(self):
        # Path traversal characters must not escape
        slug = slugify("../../etc/passwd")
        self.assertNotIn("..", slug)
        self.assertNotIn("/", slug)
        self.assertEqual(slug, "etc-passwd")

    def test_empty_fallback(self):
        self.assertEqual(slugify(""), "topic")
        self.assertEqual(slugify("   "), "topic")
        self.assertEqual(slugify("---"), "topic")

    def test_max_length(self):
        long_topic = "a" * 100
        self.assertLessEqual(len(slugify(long_topic)), 60)


class TestWithRetry(unittest.TestCase):
    @patch("time.sleep")
    def test_success_first_try(self, mock_sleep):
        fn = MagicMock(return_value="OK")
        res = with_retry(fn, attempts=3)
        self.assertEqual(res, "OK")
        self.assertEqual(fn.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("time.sleep")
    def test_retry_on_retryable_error(self, mock_sleep):
        fn = MagicMock(side_effect=[RetryableError("rate limited"), "SUCCESS"])
        res = with_retry(fn, attempts=3, base=0.1)
        self.assertEqual(res, "SUCCESS")
        self.assertEqual(fn.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @patch("time.sleep")
    def test_respects_retry_after(self, mock_sleep):
        fn = MagicMock(side_effect=[RetryableError("wait", retry_after=5.0), "OK"])
        res = with_retry(fn, attempts=3, base=0.1)
        self.assertEqual(res, "OK")
        mock_sleep.assert_called_with(5.0)

    @patch("time.sleep")
    def test_gives_up_after_attempts_without_extra_sleep(self, mock_sleep):
        fn = MagicMock(side_effect=RetryableError("persistent error"))
        with self.assertRaises(RetryableError):
            with_retry(fn, attempts=3, base=0.1)
        self.assertEqual(fn.call_count, 3)
        # Should sleep only between attempts (2 times for 3 attempts), not after the final failure
        self.assertEqual(mock_sleep.call_count, 2)

    @patch("time.sleep")
    def test_no_retry_on_fatal_error(self, mock_sleep):
        req = httpx.Request("GET", "https://example.com")
        resp = httpx.Response(400, request=req)
        fatal_error = httpx.HTTPStatusError("Bad Request", request=req, response=resp)

        fn = MagicMock(side_effect=fatal_error)
        with self.assertRaises(httpx.HTTPStatusError):
            with_retry(fn, attempts=3)
        self.assertEqual(fn.call_count, 1)
        mock_sleep.assert_not_called()


class TestCheckCitations(unittest.TestCase):
    def setUp(self):
        self.valid_sources = [
            {"n": 1, "url": "https://arxiv.org/abs/2501.00001", "title": "Paper 1", "source": "arxiv"},
            {"n": 2, "url": "https://huggingface.co/papers/2501.00002", "title": "Paper 2", "source": "hf-search"},
            {"n": 3, "url": "https://example.org/blog", "title": "Blog 3", "source": "web"},
        ]
        self.valid_report = """# Comprehensive Survey

## TL;DR
- Key finding one [1].
- Key finding two [2, 3].

## Background
Introductory text with citation [1].

## Architectural Advances
Comparison of methods [2] and modern approaches [3].

## Trends and open problems
Future directions [1-3].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025-01-01)
[2] Paper 2. hf-search. https://huggingface.co/papers/2501.00002 (2025-01-02)
[3] Blog 3. web. https://example.org/blog (2025-01-03)
"""

    def test_valid_report_passes(self):
        problems = check(self.valid_report, self.valid_sources)
        self.assertEqual(problems, [])

    def test_missing_references_heading(self):
        bad_report = "# Survey\nText citing [1].\n"
        problems = check(bad_report, self.valid_sources)
        self.assertTrue(any("missing '## References' heading" in p for p in problems))

    def test_uncited_source_flagged(self):
        # Report only cites [1] and [2], missing [3]
        incomplete_report = """# Survey
Text citing [1] and [2].

## References
[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025-01-01)
[2] Paper 2. hf-search. https://huggingface.co/papers/2501.00002 (2025-01-02)
[3] Blog 3. web. https://example.org/blog (2025-01-03)
"""
        problems = check(incomplete_report, self.valid_sources)
        self.assertTrue(any("never cited" in p for p in problems))

    def test_code_block_citations_ignored(self):
        # [99] in a code block should not be treated as a real citation
        report_with_code = self.valid_report.replace(
            "## Background",
            "## Background\nHere is code: `[99]` and:\n```\n[88]\n```"
        )
        problems = check(report_with_code, self.valid_sources)
        self.assertEqual(problems, [])

    def test_multiple_urls_in_one_reference_line(self):
        bad_ref_report = self.valid_report.replace(
            "[1] Paper 1. arxiv. https://arxiv.org/abs/2501.00001 (2025-01-01)",
            "[1] Paper 1 and 2. https://arxiv.org/abs/2501.00001 https://huggingface.co/papers/2501.00002"
        )
        problems = check(bad_ref_report, self.valid_sources)
        self.assertTrue(any("multiple URLs" in p for p in problems))


if __name__ == "__main__":
    unittest.main()
