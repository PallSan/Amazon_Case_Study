from __future__ import annotations

import argparse
import html
from pathlib import Path

from .engine import detect_systemic_events, generate_wbr_summary, rank_station_risks
from .io import load_station_metrics


def _severity_class(severity: str) -> str:
    if severity == "critical":
        return "severity-red"
    if severity == "high":
        return "severity-red"
    if severity == "moderate":
        return "severity-yellow"
    return "severity-green"


def build_html_report(input_csv: str, top: int = 10) -> str:
    metrics = load_station_metrics(input_csv)
    ranked = rank_station_risks(metrics)
    systemic = detect_systemic_events(metrics)
    summary = generate_wbr_summary(ranked, systemic)

    top = max(1, min(top, 50))
    top_risks = ranked[:top]

    risk_rows = "".join(
        (
            "<tr>"
            f"<td><a href='#station-{html.escape(r.station_id)}'>{html.escape(r.station_id)}</a></td>"
            f"<td>{r.score:.2f}</td>"
            f"<td><span class='severity-pill {_severity_class(r.severity)}'>{html.escape(r.severity.title())}</span></td>"
            f"<td>{html.escape('; '.join(r.root_causes[:3]))}</td>"
            f"<td>{html.escape('; '.join(r.interventions[:3]))}</td>"
            "</tr>"
        )
        for r in top_risks
    )

    station_cards = "".join(
        (
            f"<section id='station-{html.escape(r.station_id)}' class='card'>"
            f"<h3>{html.escape(r.station_id)} <span class='severity-pill {_severity_class(r.severity)}'>{html.escape(r.severity.title())}</span></h3>"
            f"<p><strong>Risk score:</strong> {r.score:.2f}</p>"
            f"<p><strong>Explanation:</strong> {html.escape(r.explanation)}</p>"
            f"<p><strong>Likely root causes:</strong> {html.escape('; '.join(r.root_causes[:3]))}</p>"
            f"<p><strong>Suggested interventions:</strong> {html.escape('; '.join(r.interventions[:3]))}</p>"
            "<p><a href='#top'>Back to top</a></p>"
            "</section>"
        )
        for r in top_risks
    )

    systemic_rows = (
        "".join(f"<li>{html.escape(event.summary)}</li>" for event in systemic)
        if systemic
        else "<li>No systemic events detected in the selected window.</li>"
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Regional Operations Intelligence Copilot - Demo Report</title>
  <style>
    body {{ font-family: Inter, Arial, sans-serif; margin: 24px; background: #f5f7fb; color: #121826; }}
    .card {{ background: #fff; border-radius: 10px; padding: 16px; margin-bottom: 16px; box-shadow: 0 2px 6px rgba(18,24,38,.08); }}
    h1 {{ margin: 0 0 8px; }}
    h2 {{ margin-top: 0; }}
    .meta {{ color: #4b5563; margin: 0; }}
    table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
    th, td {{ padding: 8px; border-bottom: 1px solid #e5e7eb; text-align: left; vertical-align: top; }}
    th {{ background: #f8fafc; }}
    .pill {{ display: inline-block; padding: 4px 8px; border-radius: 999px; background: #e0ecff; font-size: 12px; }}
    .severity-pill {{ display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; }}
    .severity-red {{ background: #fee2e2; color: #991b1b; }}
    .severity-yellow {{ background: #fef3c7; color: #92400e; }}
    .severity-green {{ background: #dcfce7; color: #166534; }}
    .nav {{ position: sticky; top: 0; z-index: 10; display: flex; gap: 14px; padding: 10px 12px; background: #ffffffd9; border: 1px solid #e5e7eb; border-radius: 10px; backdrop-filter: blur(4px); margin-bottom: 16px; }}
    .nav a {{ text-decoration: none; color: #1d4ed8; font-weight: 600; }}
    .nav a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body id=\"top\">
  <nav class=\"nav\">
    <a href=\"#summary\">WBR Summary</a>
    <a href=\"#top-risks\">Top Risks</a>
    <a href=\"#systemic\">Systemic Signals</a>
    <a href=\"#station-details\">Station Details</a>
  </nav>

  <section class=\"card\">
    <h1>Regional Operations Intelligence Copilot</h1>
    <p class=\"meta\">Standalone HTML demo report generated from: <code>{html.escape(input_csv)}</code></p>
    <p><span class=\"pill\">MVP</span> Risk prioritization + systemic signal detection + WBR narrative</p>
  </section>

  <section id=\"summary\" class=\"card\">
    <h2>WBR Summary</h2>
    <p>{html.escape(summary)}</p>
  </section>

  <section id=\"top-risks\" class=\"card\">
    <h2>Top {top} Station Risks</h2>
    <table>
      <thead>
        <tr><th>Station</th><th>Score</th><th>Severity</th><th>Likely Root Causes</th><th>Suggested Interventions</th></tr>
      </thead>
      <tbody>
        {risk_rows}
      </tbody>
    </table>
  </section>

  <section id=\"systemic\" class=\"card\">
    <h2>Systemic Signals</h2>
    <ul>{systemic_rows}</ul>
  </section>

  <section id=\"station-details\">
    <h2>Station Drill-Down</h2>
    {station_cards}
  </section>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate standalone HTML demo report")
    parser.add_argument("--input", default="data/sample_station_metrics.csv", help="CSV input path")
    parser.add_argument("--output", default="demo/index.html", help="HTML output path")
    parser.add_argument("--top", type=int, default=10, help="Top stations to include")
    args = parser.parse_args()

    html_doc = build_html_report(input_csv=args.input, top=args.top)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_doc, encoding="utf-8")
    print(f"Wrote HTML report to {out}")


if __name__ == "__main__":
    main()
