from __future__ import annotations

import argparse
from collections import defaultdict

from .engine import detect_systemic_events, generate_wbr_summary, rank_station_risks
from .io import load_station_metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Regional Operations Intelligence Copilot MVP")
    parser.add_argument("--input", required=True, help="Path to daily station metrics CSV")
    parser.add_argument("--top", type=int, default=5, help="Number of highest-risk stations to print")
    args = parser.parse_args()

    metrics = load_station_metrics(args.input)
    ranked = rank_station_risks(metrics)
    systemic = detect_systemic_events(metrics)

    print("=== Top Station Risks ===")
    for item in ranked[: args.top]:
        print(f"- {item.station_id} | score={item.score:.2f} | severity={item.severity}")
        print(f"  explanation: {item.explanation}")
        print(f"  likely root causes: {item.root_causes[0]}; {item.root_causes[1]}; {item.root_causes[2]}")
        print(f"  interventions: {item.interventions[0]}; {item.interventions[1]}; {item.interventions[2]}")

    print("\n=== Systemic Signals ===")
    if not systemic:
        print("- none")
    for event in systemic:
        print(f"- {event.summary}")

    print("\n=== WBR Summary ===")
    print(generate_wbr_summary(ranked, systemic))

    by_region = defaultdict(list)
    for row in ranked:
        by_region[row.region].append(row)

    print("\n=== Regional Snapshot ===")
    for region, rows in by_region.items():
        avg = sum(item.score for item in rows) / len(rows)
        print(f"- {region}: stations={len(rows)} avg_risk={avg:.2f}")


if __name__ == "__main__":
    main()
