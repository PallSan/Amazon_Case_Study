import unittest

from src.copilot.html_report import build_html_report


class HtmlReportTests(unittest.TestCase):
    def test_build_html_report_contains_expected_sections(self):
        report = build_html_report("data/sample_station_metrics.csv", top=5)
        self.assertIn("WBR Summary", report)
        self.assertIn("Top 5 Station Risks", report)
        self.assertIn("Systemic Signals", report)


if __name__ == "__main__":
    unittest.main()
