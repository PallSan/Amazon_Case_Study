from __future__ import annotations

import argparse
import html
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .engine import detect_systemic_events, generate_wbr_summary, rank_station_risks
from .io import load_station_metrics


class CopilotWebHandler(BaseHTTPRequestHandler):
    """Minimal standard-library UI for viewing regional risk outputs."""

    def do_GET(self) -> None:  # noqa: N802 (HTTP verb naming)
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)

        input_path = query.get("input", ["data/sample_station_metrics.csv"])[0]
        top = int(query.get("top", ["5"])[0])

        content = self._render_page(input_path=input_path, top=top)
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(content.encode("utf-8"))

    def _render_page(self, input_path: str, top: int) -> str:
        safe_input_path = html.escape(input_path)
        top = max(1, min(top, 25))

        result_html = ""
        try:
            metrics = load_station_metrics(input_path)
            ranked = rank_station_risks(metrics)
            systemic = detect_systemic_events(metrics)
            summary = generate_wbr_summary(ranked, systemic)

            rows = "".join(
                (
                    "<tr>"
                    f"<td>{html.escape(item.station_id)}</td>"
                    f"<td>{item.score:.2f}</td>"
                    f"<td>{html.escape(item.severity)}</td>"
                    f"<td>{html.escape(item.explanation)}</td>"
                    "</tr>"
                )
                for item in ranked[:top]
            )

            systemic_rows = (
                "".join(
                    f"<li>{html.escape(event.summary)}</li>"
                    for event in systemic
                )
                if systemic
                else "<li>none</li>"
            )

            result_html = f"""
                <section class=\"card\">
                    <h2>WBR Summary</h2>
                    <p>{html.escape(summary)}</p>
                </section>
                <section class=\"card\">
                    <h2>Top Station Risks</h2>
                    <table>
                        <thead><tr><th>Station</th><th>Score</th><th>Severity</th><th>Explanation</th></tr></thead>
                        <tbody>{rows}</tbody>
                    </table>
                </section>
                <section class=\"card\">
                    <h2>Systemic Signals</h2>
                    <ul>{systemic_rows}</ul>
                </section>
            """
        except Exception as exc:  # broad to keep UI resilient in MVP
            result_html = f"""
                <section class=\"card error\">
                    <h2>Could not load metrics</h2>
                    <p>{html.escape(str(exc))}</p>
                </section>
            """

        return f"""
        <!doctype html>
        <html>
          <head>
            <meta charset=\"utf-8\" />
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <title>Regional Operations Intelligence Copilot</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 24px; background: #f7f8fa; color: #111; }}
                .header {{ margin-bottom: 16px; }}
                .card {{ background: white; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
                .error {{ border-left: 4px solid #b00020; }}
                form {{ display: flex; gap: 12px; align-items: end; flex-wrap: wrap; }}
                label {{ display: flex; flex-direction: column; font-size: 14px; gap: 4px; }}
                input {{ padding: 8px; min-width: 260px; }}
                button {{ padding: 9px 14px; background: #0057b8; color: white; border: none; border-radius: 6px; cursor: pointer; }}
                table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
                th, td {{ border-bottom: 1px solid #e6e7ea; padding: 8px; text-align: left; vertical-align: top; }}
                th {{ background: #fafbfc; }}
            </style>
          </head>
          <body>
            <div class=\"header\">
                <h1>Regional Operations Intelligence Copilot (MVP UI)</h1>
                <p>Decision-support dashboard for station risk prioritization and WBR summary generation.</p>
            </div>

            <section class=\"card\">
                <form method=\"get\" action=\"/\">
                    <label>
                        Metrics CSV Path
                        <input type=\"text\" name=\"input\" value=\"{safe_input_path}\" />
                    </label>
                    <label>
                        Top stations
                        <input type=\"number\" name=\"top\" value=\"{top}\" min=\"1\" max=\"25\" />
                    </label>
                    <button type=\"submit\">Run Analysis</button>
                </form>
            </section>

            {result_html}
          </body>
        </html>
        """


def run_server(host: str, port: int) -> None:
    server = HTTPServer((host, port), CopilotWebHandler)
    print(f"Serving Copilot UI at http://{host}:{port}")
    server.serve_forever()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Copilot MVP web UI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
