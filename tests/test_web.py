import unittest

from src.copilot.web import CopilotWebHandler


class WebRenderTests(unittest.TestCase):
    def test_render_page_contains_sections(self):
        handler = CopilotWebHandler
        html = handler._render_page(handler, "data/sample_station_metrics.csv", 3)
        self.assertIn("WBR Summary", html)
        self.assertIn("Top Station Risks", html)
        self.assertIn("Systemic Signals", html)


if __name__ == "__main__":
    unittest.main()
