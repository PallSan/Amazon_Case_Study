from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import List

from .models import StationMetric


def load_station_metrics(csv_path: str) -> List[StationMetric]:
    path = Path(csv_path)
    rows: List[StationMetric] = []

    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rows.append(
                StationMetric(
                    date=datetime.strptime(row["date"], "%Y-%m-%d").date(),
                    region=row["region"],
                    station_id=row["station_id"],
                    sla_miss_pct=float(row["sla_miss_pct"]),
                    dwell_variance_hours=float(row["dwell_variance_hours"]),
                    staffing_delta_pct=float(row["staffing_delta_pct"]),
                    volume_mismatch_pct=float(row["volume_mismatch_pct"]),
                    dispatch_delay_minutes=float(row["dispatch_delay_minutes"]),
                    late_linehaul_pct=float(row["late_linehaul_pct"]),
                )
            )

    return rows
