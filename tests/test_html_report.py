import unittest

from src.copilot.html_report import build_html_report


class HtmlReportTests(unittest.TestCase):
    def test_build_html_report_contains_expected_sections(self):
        report = build_html_report("data/sample_station_metrics.csv", top=5)
        self.assertIn("WBR Summary", report)
        self.assertIn("Top 5 Station Risks", report)
        self.assertIn("Systemic Signals", report)

    def test_report_has_navigation_and_severity_colors(self):
        report = build_html_report("data/sample_station_metrics.csv", top=5)
        self.assertIn("href=\"#summary\"", report)
        self.assertIn("href=\"#top-risks\"", report)
        self.assertIn("severity-red", report)
        self.assertIn("severity-yellow", report)
        self.assertIn("severity-green", report)

    def test_report_has_chat_window(self):
        report = build_html_report("data/sample_station_metrics.csv", top=5)
        self.assertIn("Ask Copilot (Demo Chat)", report)
        self.assertIn("id=\"chat-input\"", report)
        self.assertIn("id=\"chat-send\"", report)
        self.assertIn("function answerQuestion", report)


if __name__ == "__main__":
    unittest.main()
