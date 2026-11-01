import unittest

from exporters.manifest import normalize_response, summarize


class ManifestTests(unittest.TestCase):
    def test_direct_video_url_is_preserved_exactly(self):
        url = "https://cdn.example.test/a/master.m3u8?token=opaque%2Fvalue"
        records = normalize_response({"data": [{"id": 7, "Title": "Lecture", "material_type": "VIDEO", "video_url": url}]}, platform="appx")
        self.assertEqual(records[0]["url"], url)
        self.assertEqual(records[0]["kind"], "video")

    def test_pdf_attachment_is_not_claimed_as_interactive_test(self):
        url = "https://cdn.example.test/test-paper.pdf?sig=abc"
        records = normalize_response({"data": [{"id": 8, "Title": "Mock test", "material_type": "TEST", "pdf_link": url}]}, platform="appx")
        self.assertEqual(records[0]["kind"], "test_attachment")
        self.assertEqual(records[0]["url"], url)

    def test_questions_are_preserved_when_returned(self):
        payload = {"data": [{"id": 9, "title": "Quiz", "material_type": "TEST", "questions": [{"id": 1, "text": "Q?", "options": ["A", "B"], "explanation": "Because"}]}]}
        records = normalize_response(payload, platform="appx")
        self.assertEqual(records[0]["kind"], "test_series")
        self.assertEqual(records[0]["status"], "unsupported")
        self.assertEqual(records[0]["test_data"]["questions"][0]["text"], "Q?")

    def test_never_constructs_url_from_thumbnail_or_path(self):
        records = normalize_response({"data": [{"id": 10, "Title": "No URL", "material_type": "VIDEO", "thumbnail": "https://img.example.test/x.jpg", "path": "videos/10"}]}, platform="classplus")
        self.assertIsNone(records[0]["url"])
        self.assertEqual(records[0]["status"], "missing_url")

    def test_duplicate_id_and_url_deduplicated(self):
        item = {"id": 11, "title": "PDF", "material_type": "PDF", "pdf_url": "https://cdn.example.test/a.pdf"}
        records = normalize_response({"data": [item, dict(item)]}, platform="appx")
        self.assertEqual(len(records), 1)

    def test_summary_counts(self):
        records = [{"status": "exported"}, {"status": "missing_url"}, {"status": "unsupported"}, {"status": "unauthorized"}]
        self.assertEqual(summarize(records), {"discovered": 4, "exported": 1, "missing_url": 1, "unsupported": 1, "failed": 0, "unauthorized": 1})


if __name__ == "__main__":
    unittest.main()
