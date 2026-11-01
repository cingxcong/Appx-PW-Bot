import unittest

from exporters.txt_input import ManifestInputError, parse_txt_manifest


class TxtInputTests(unittest.TestCase):
    def test_raw_url_and_title_url_formats(self):
        parsed = parse_txt_manifest(
            "# course export\n"
            "https://cdn.example.test/a.m3u8?sig=a%2Fb\n"
            "Lecture 02: https://cdn.example.test/b.mp4\n"
        )
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0]["title"], "Item 1")
        self.assertEqual(parsed[0]["url"], "https://cdn.example.test/a.m3u8?sig=a%2Fb")
        self.assertEqual(parsed[1]["title"], "Lecture 02")

    def test_deduplicates_exact_urls_and_keeps_first_title(self):
        parsed = parse_txt_manifest(
            "First: https://cdn.example.test/a.mp4\n"
            "Second: https://cdn.example.test/a.mp4\n"
        )
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["title"], "First")

    def test_ignores_non_http_and_embedded_credentials(self):
        parsed = parse_txt_manifest(
            "ftp://example.test/file.mp4\n"
            "https://user:pass@example.test/video.mp4\n"
            "javascript:alert(1)\n"
        )
        self.assertEqual(parsed, [])

    def test_ignores_comments_and_non_url_lines(self):
        parsed = parse_txt_manifest(
            "# comment\n"
            "Some explanatory text\n"
            "Notes: https://example.test/notes.pdf\n"
        )
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["line_number"], 3)

    def test_rejects_oversized_input(self):
        with self.assertRaises(ManifestInputError):
            parse_txt_manifest("x" * (2 * 1024 * 1024 + 1))


if __name__ == "__main__":
    unittest.main()
