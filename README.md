# Regional Operations Intelligence Copilot (MVP)

This repository contains a lightweight MVP for a **Delivery Station Regional Operations Intelligence Copilot**.

## What this MVP does

- Aggregates daily station-level operational metrics.
- Computes a transparent, weighted **Operational Risk Score**.
- Distinguishes **systemic** (multi-station correlated) vs **localized** risks.
- Suggests top intervention actions by risk driver.
- Generates **WBR-ready** regional narrative summaries.

## MVP scope

Included:
- Rule-based risk engine (interpretable and tunable)
- Risk ranking and top-contributor explanation
- Systemic-event detection via correlated anomaly windows
- Structured narrative generation

Not included:
- Real-time ingestion
- Predictive forecasting
- Staffing optimization
- External LLM calls (template-based generation is used for determinism)

## Quick start

```bash
python -m src.copilot.cli --input data/sample_station_metrics.csv --top 5
```

## Run tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

## Run web UI

```bash
python -m src.copilot.web --port 8000
```

Then open `http://localhost:8000` and point the UI at your metrics CSV path.

## Generate standalone HTML demo

```bash
python -m src.copilot.html_report --input data/sample_station_metrics.csv --output demo/index.html --top 8
```

Open `demo/index.html` directly in a browser for a shareable demo artifact.

## Data contract

Expected input columns:
- `date` (YYYY-MM-DD)
- `region`
- `station_id`
- `sla_miss_pct`
- `dwell_variance_hours`
- `staffing_delta_pct`
- `volume_mismatch_pct`
- `dispatch_delay_minutes`
- `late_linehaul_pct`

All metric percentages are expected as absolute percentage values (e.g., `7.5` means 7.5%).
