from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List


@dataclass(frozen=True)
class StationMetric:
    date: date
    region: str
    station_id: str
    sla_miss_pct: float
    dwell_variance_hours: float
    staffing_delta_pct: float
    volume_mismatch_pct: float
    dispatch_delay_minutes: float
    late_linehaul_pct: float


@dataclass
class RiskResult:
    station_id: str
    region: str
    date: date
    score: float
    severity: str
    contributors: Dict[str, float]
    root_causes: List[str]
    interventions: List[str]
    explanation: str


@dataclass
class SystemicEvent:
    region: str
    date: date
    stations: List[str] = field(default_factory=list)
    trigger_metric: str = ""
    confidence: float = 0.0
    summary: str = ""
