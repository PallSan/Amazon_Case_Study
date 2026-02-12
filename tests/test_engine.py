from datetime import date
import unittest

from src.copilot.engine import detect_systemic_events, rank_station_risks, score_station
from src.copilot.models import StationMetric


class RiskEngineTests(unittest.TestCase):
    def test_score_station_returns_high_severity_for_large_deviation(self):
        row = StationMetric(
            date=date(2026, 1, 18),
            region="US-WEST-R1",
            station_id="DS-HIGH",
            sla_miss_pct=9.0,
            dwell_variance_hours=3.0,
            staffing_delta_pct=16.0,
            volume_mismatch_pct=14.0,
            dispatch_delay_minutes=42,
            late_linehaul_pct=18.0,
        )

        result = score_station(row)
        self.assertGreater(result.score, 0.55)
        self.assertIn(result.severity, {"high", "critical"})
        self.assertEqual(len(result.interventions), 3)

    def test_rank_station_risks_orders_descending(self):
        rows = [
            StationMetric(date(2026, 1, 18), "R", "A", 1, 0.5, 2, 2, 5, 1),
            StationMetric(date(2026, 1, 18), "R", "B", 7, 2.2, 8, 8, 25, 12),
            StationMetric(date(2026, 1, 18), "R", "C", 3, 1.0, 5, 4, 10, 4),
        ]

        ranked = rank_station_risks(rows)
        self.assertEqual([r.station_id for r in ranked], ["B", "C", "A"])

    def test_detect_systemic_events_flags_multi_station_pattern(self):
        rows = [
            StationMetric(date(2026, 1, 18), "R", "S1", 5, 2.0, 6, 6, 20, 12),
            StationMetric(date(2026, 1, 18), "R", "S2", 6, 2.1, 5, 7, 18, 11),
            StationMetric(date(2026, 1, 18), "R", "S3", 4.5, 1.7, 7, 8, 22, 9),
            StationMetric(date(2026, 1, 18), "R", "S4", 1, 0.4, 2, 2, 5, 2),
        ]

        events = detect_systemic_events(rows)
        self.assertEqual(len(events), 1)
        self.assertIn(events[0].trigger_metric, {"dwell_variance_hours", "late_linehaul_pct", "sla_miss_pct", "dispatch_delay_minutes"})


if __name__ == "__main__":
    unittest.main()
