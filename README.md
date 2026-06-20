# ParkPulse

**Parking-Induced Congestion Intelligence · Flipkart GRID PS1**

An end-to-end enforcement intelligence system that detects illegal parking hotspots across Bangalore, ranks them by a transparent priority score, forecasts next-day violation volume, and allocates patrol units via constrained optimization.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://huggingface.co/spaces/Adit555/ParkPulse)

---

## Live Demo

→ **[Hugging Face Space](https://huggingface.co/spaces/Adit555/ParkPulse)**
---

## What It Does

| Stage | Module | Output |
|---|---|---|
| Clean & normalise | `pipeline/clean.py` | 298,450 records, UTC→IST corrected, severity-weighted |
| Geographic clustering | `pipeline/hotspots.py` | 236 DBSCAN clusters across Bangalore |
| Named-hotspot ranking | `models/ppi.py` | PPI score + tier for 164 real junctions |
| Violation forecast | `models/forecast.py` | LightGBM next-day predictions, top-15 junctions |
| Patrol allocation | `models/allocation.py` | MILP unit assignment, optimal in under 1 second |
| Dashboard | `dashboard/app.py` | 4-screen Streamlit app |

---

## Quick Start

```bash
pip install -r requirements.txt

# Place the raw CSV in data/raw/ before running
python -m src.pipeline.run_all      # ~20 seconds end-to-end

streamlit run src/dashboard/app.py
```

The pipeline regenerates every artifact from the raw CSV in one command. The dashboard reads precomputed Parquet files — no live model inference during the demo.

---

## Project Structure

```
src/
├── config.py               # Single source of truth for all parameters
├── pipeline/
│   ├── clean.py            # Phase 1 — parse, timezone fix, validation filter
│   ├── aggregate.py        # Phase 2 — per-junction daily aggregation
│   ├── hotspots.py         # Phase 2 — DBSCAN geographic clustering
│   └── run_all.py          # Entry point — runs all phases in order
├── models/
│   ├── ppi.py              # Parking Pressure Index + sensitivity check
│   ├── forecast.py         # LightGBM/XGBoost + naive baselines
│   └── allocation.py       # MILP patrol allocation (PuLP)
└── dashboard/
    ├── app.py              # Streamlit app — 4 pages
    ├── components.py       # Charts, maps, badges
    └── data_loader.py      # Cached artifact readers

data/
├── raw/                    # Place source CSV here (gitignored)
└── processed/              # Pipeline outputs (gitignored, regenerable)

docs/
└── TECHNICAL_OVERVIEW.md   # Full methodology, module specs, metric table
```

---

## Key Numbers

| | |
|---|---|
| Dataset | 298,450 records · Nov 2023 – Apr 2024 · Bangalore |
| Validated records | 115,400 (`approved` status only) |
| Named junctions ranked | 164 (49.5% of records had no usable junction name — handled explicitly) |
| DBSCAN clusters | 236 geographic hotspots |
| Forecast MAE | 11.40 violations/day (Mar 2024 validation set, 15 junctions) |
| Beats 7-day rolling baseline | Yes — 11.40 vs 12.33 |
| PPI sensitivity | Stable — 14–15/15 top-15 overlap across all ±10% weight perturbations |
| Pipeline runtime | ~20 seconds on a laptop |
| Dashboard load | Under 2 seconds (all precomputed) |

---

## Dashboard Pages

**Overview** — Bangalore map with PPI-tiered hotspot circles, top-5 ranked list, full junction table. Filter by police station.

**Hotspot Detail** — Per-junction drill-down: PPI component breakdown bars, hourly and day-of-week enforcement patterns, vehicle type mix, violation forecast with backtested error band.

**Patrol Allocation** — Set available patrol units → MILP distributes them optimally in under a second. Deployment map with numbered markers per hotspot.

**Data & Methodology** — Full cleaning steps, PPI formula, severity weight table, backtest results, known limitations. Designed to pre-empt judge questions before they're asked.

---

## Design Decisions

**Why not RL?**
RL needs outcome feedback — did violations drop after a patrol was deployed? That data doesn't exist yet. MILP is fully explainable, solves in milliseconds, and is the right tool until post-deployment outcome data is collected.

**Why is PPI called a "proxy"?**
No speed or volume data exists in this dataset. PPI is built from violation counts, severity weights, repeat offenders, and persistence — a legitimate enforcement-priority signal, but not a measured traffic-impact metric. Labelled honestly everywhere it appears.

**Why is 49.5% of the data "unattributable"?**
The raw data contains `"No Junction"` as a literal field value for violations recorded without a junction name. These span all 54 police stations and every part of the city — not a real location. They contribute to geographic DBSCAN clustering (which uses lat/long) but are excluded from the named-hotspot ranking. Documented on the Methodology page, not hidden.

---

## Tech Stack

Python 3.11 · pandas · scikit-learn (DBSCAN) · LightGBM · XGBoost · PuLP · Streamlit · Folium · Plotly · PyArrow

All open-source. No paid API keys. Runs fully offline.

---

## Documentation

Full methodology, module specs, severity weight table, and metric details: [`docs/TECHNICAL_OVERVIEW.md`](docs/TECHNICAL_OVERVIEW.md)
