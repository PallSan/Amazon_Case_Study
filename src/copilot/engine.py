from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Dict, Iterable, List

from .models import RiskResult, StationMetric, SystemicEvent


# Interpretable starting weights. Tunable per-region in pilot.
RISK_WEIGHTS: Dict[str, float] = {
    "sla_miss_pct": 0.30,
    "dwell_variance_hours": 0.22,
    "staffing_delta_pct": 0.16,
    "volume_mismatch_pct": 0.14,
    "dispatch_delay_minutes": 0.10,
    "late_linehaul_pct": 0.08,
}

# Heuristic normalization denominators for metric scaling (MVP assumption).
NORMALIZERS: Dict[str, float] = {
    "sla_miss_pct": 10.0,
    "dwell_variance_hours": 4.0,
    "staffing_delta_pct": 20.0,
    "volume_mismatch_pct": 20.0,
    "dispatch_delay_minutes": 60.0,
    "late_linehaul_pct": 25.0,
}

ROOT_CAUSE_LOOKUP: Dict[str, List[str]] = {
    "sla_miss_pct": [
        "Capacity-demand mismatch during peak window",
        "Sort-to-dispatch handoff instability",
        "Carrier departure adherence gaps",
    ],
    "dwell_variance_hours": [
        "Late inbound linehaul causing downstream queueing",
        "Yard congestion and unload cycle delays",
        "Sort throughput constrained by staffing mix",
    ],
    "staffing_delta_pct": [
        "Planned vs actual labor shortfall",
        "High same-day absence concentration",
        "Intra-shift allocation imbalance",
    ],
    "volume_mismatch_pct": [
        "Forecast miss from upstream dispatch profile",
        "Uneven wave sequencing across stations",
        "Unexpected route assignment volatility",
    ],
    "dispatch_delay_minutes": [
        "Route launch sequencing delay",
        "Trailer/vehicle readiness gaps",
        "Last-mile handoff congestion",
    ],
    "late_linehaul_pct": [
        "Linehaul departure non-adherence upstream",
        "Hub-to-station transfer bottleneck",
        "Carrier schedule reliability degradation",
    ],
}

INTERVENTION_LOOKUP: Dict[str, List[str]] = {
    "sla_miss_pct": [
        "Trigger same-day exception review with top 3 impacted routes.",
        "Reprioritize dispatch sequence for at-risk customer promise windows.",
        "Escalate carrier adherence checkpoint before cutoff.",
    ],
    "dwell_variance_hours": [
        "Execute inbound smoothing for the next 2 cycles.",
        "Stand up temporary unload surge plan for late arrivals.",
        "Rebalance sort labor to high-queue zones for first 4 hours.",
    ],
    "staffing_delta_pct": [
        "Activate labor contingency roster for next shift.",
        "Reallocate cross-trained associates to constrained process steps.",
        "Institute hourly staffing adherence huddles until variance <5%.",
    ],
    "volume_mismatch_pct": [
        "Coordinate upstream dispatch throttling for overloaded windows.",
        "Shift non-critical volume to adjacent lower-risk stations.",
        "Tighten 24-hour forecast reconciliation with network planning.",
    ],
    "dispatch_delay_minutes": [
        "Prioritize delayed wave routes with SLA-critical packages.",
        "Create launch readiness checklist at T-30 minutes.",
        "Escalate route assignment blockers to regional control tower.",
    ],
    "late_linehaul_pct": [
        "Escalate linehaul adherence review with upstream node owners.",
        "Pre-stage unload teams aligned to expected delayed arrivals.",
        "Open contingency dock allocation for late trailers.",
    ],
}


def _clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def _normalize(metric_name: str, raw_value: float) -> float:
    denom = NORMALIZERS[metric_name]
    return _clamp(raw_value / denom)


def _severity(score: float) -> str:
    if score >= 0.75:
        return "critical"
    if score >= 0.55:
        return "high"
    if score >= 0.35:
        return "moderate"
    return "low"


def score_station(metric: StationMetric) -> RiskResult:
    contributors: Dict[str, float] = {}
    weighted_total = 0.0

    for metric_name, weight in RISK_WEIGHTS.items():
        normalized = _normalize(metric_name, getattr(metric, metric_name))
        contribution = normalized * weight
        contributors[metric_name] = round(contribution, 4)
        weighted_total += contribution

    score = round(_clamp(weighted_total), 4)
    sorted_drivers = sorted(contributors.items(), key=lambda item: item[1], reverse=True)
    top_drivers = [name for name, _ in sorted_drivers[:3]]

    root_causes = [ROOT_CAUSE_LOOKUP[name][0] for name in top_drivers]
    interventions = [INTERVENTION_LOOKUP[name][0] for name in top_drivers]

    readable_drivers = ", ".join(top_drivers)
    explanation = (
        f"Risk score {score:.2f} driven primarily by {readable_drivers}. "
        f"Severity classified as {_severity(score)} based on composite weighted deviation."
    )

    return RiskResult(
        station_id=metric.station_id,
        region=metric.region,
        date=metric.date,
        score=score,
        severity=_severity(score),
        contributors=contributors,
        root_causes=root_causes,
        interventions=interventions,
        explanation=explanation,
    )


def rank_station_risks(station_metrics: Iterable[StationMetric]) -> List[RiskResult]:
    results = [score_station(item) for item in station_metrics]
    return sorted(results, key=lambda result: result.score, reverse=True)


def detect_systemic_events(station_metrics: Iterable[StationMetric]) -> List[SystemicEvent]:
    metrics = list(station_metrics)
    if not metrics:
        return []

    by_region_date: Dict[tuple, List[StationMetric]] = {}
    for item in metrics:
        by_region_date.setdefault((item.region, item.date), []).append(item)

    events: List[SystemicEvent] = []
    for (region, day), rows in by_region_date.items():
        if len(rows) < 3:
            continue

        metric_thresholds = {
            "dwell_variance_hours": 1.5,
            "late_linehaul_pct": 8.0,
            "dispatch_delay_minutes": 20.0,
            "sla_miss_pct": 4.0,
        }

        exceedance_counter: Counter = Counter()
        station_by_metric: Dict[str, List[str]] = {k: [] for k in metric_thresholds.keys()}

        for row in rows:
            for metric_name, threshold in metric_thresholds.items():
                if getattr(row, metric_name) >= threshold:
                    exceedance_counter[metric_name] += 1
                    station_by_metric[metric_name].append(row.station_id)

        trigger_metric, trigger_count = exceedance_counter.most_common(1)[0] if exceedance_counter else (None, 0)
        if not trigger_metric:
            continue

        prevalence = trigger_count / len(rows)
        if trigger_count >= 3 and prevalence >= 0.4:
            confidence = round(min(0.95, 0.5 + (prevalence / 2)), 2)
            stations = sorted(set(station_by_metric[trigger_metric]))
            events.append(
                SystemicEvent(
                    region=region,
                    date=day,
                    stations=stations,
                    trigger_metric=trigger_metric,
                    confidence=confidence,
                    summary=(
                        f"Systemic signal detected: {trigger_metric} breached in {trigger_count}/{len(rows)} "
                        f"stations ({prevalence:.0%}) with confidence {confidence:.2f}."
                    ),
                )
            )

    return sorted(events, key=lambda event: event.confidence, reverse=True)


def generate_wbr_summary(ranked_risks: List[RiskResult], systemic_events: List[SystemicEvent]) -> str:
    if not ranked_risks:
        return "No risks detected for the selected window."

    top = ranked_risks[:3]
    avg_risk = mean(r.score for r in ranked_risks)
    critical = [r for r in ranked_risks if r.severity == "critical"]

    lead = (
        f"Regional risk posture is {('elevated' if avg_risk >= 0.5 else 'stable')} "
        f"with average score {avg_risk:.2f}. "
        f"{len(critical)} station(s) are currently in critical status."
    )

    station_lines = " ".join(
        f"{r.station_id} scored {r.score:.2f} ({r.severity}) driven by {', '.join(list(r.contributors.keys())[:2])}."
        for r in top
    )

    if systemic_events:
        systemic = systemic_events[0]
        systemic_line = (
            f"A systemic pattern was identified in {systemic.region} on {systemic.date}: "
            f"{systemic.trigger_metric} affecting {len(systemic.stations)} stations."
        )
    else:
        systemic_line = "No multi-station systemic anomaly exceeded the configured threshold."

    return " ".join([lead, station_lines, systemic_line])
