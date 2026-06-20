# ParkPulse — Parking-Induced Congestion Intelligence
**Flipkart GRID · Problem Statement 1 (PS1)**

> Detect illegal parking hotspots, quantify their enforcement priority,
> forecast next-day violation volume, and allocate patrol units optimally.

---

## Live Demo
Deployed on Hugging Face Spaces → _link to be added after deployment_

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place the raw CSV in data/raw/
#    File: jan to may police violation_anonymized791b166.csv

# 3. Run the full pipeline (clean → cluster → PPI → forecast → allocate)
python -m src.pipeline.run_all

# 4. Launch the dashboard
streamlit run src/dashboard/app.py
```

Pipeline completes in **~20 seconds** on a laptop. Dashboard cold-loads in **<2 seconds** — all heavy computation is precomputed.

---

## Project Structure

```
src/
  config.py           # All magic numbers in one place (DBSCAN eps, PPI weights, etc.)
  pipeline/
    clean.py          # Phase 1: parse, timezone-correct, filter
    aggregate.py      # Phase 2: junction_daily + temporal patterns
    hotspots.py       # Phase 2: DBSCAN geographic clustering
    run_all.py        # Single entry point — regenerates everything from raw CSV
  models/
    ppi.py            # Phase 3: Parking Pressure Index (PPI) + sensitivity check
    forecast.py       # Phase 3: LightGBM + XGBoost + baselines
    allocation.py     # Phase 4: MILP patrol allocation (PuLP)
  dashboard/
    app.py            # Streamlit app — 4 pages
    components.py     # Reusable chart + map builders
    data_loader.py    # Cached Parquet readers

data/
  raw/                # Place source CSV here (gitignored)
  processed/          # Pipeline output artifacts (gitignored, regenerable)

docs/
  PHASE6_DEMO.md      # 90-second demo script + hard-question answers
  PRD.md / TECH_SPEC.md / SCHEMA.md / DESIGN.md / APP_FLOW.md / RULES.md
```

---

## What the Pipeline Produces

| Artifact | Description |
|---|---|
| `violations_clean.parquet` | 298,450 cleaned records, UTC→IST corrected, severity-weighted |
| `junction_daily.parquet` | Validated violations per junction per day |
| `hotspots.parquet` | 236 DBSCAN geographic clusters with real labels |
| `ppi_scores.parquet` | PPI score + tier for 164 named junctions |
| `forecast_results.parquet` | LightGBM predictions for top-15 junctions |
| `allocation_results.parquet` | MILP patrol assignments for unit counts 5–25 |

---

## Key Findings

- **147,880 records (49.5%)** carry no usable junction attribution (`"No Junction"`) — kept in the clean table and fed to DBSCAN (lat/lon clustering), excluded from named-hotspot ranking.
- Timestamps are **UTC**. Converted to IST — enforcement peaks at **10:00 IST**, consistent with morning sweep timing, not offense-occurrence time.
- **28.9%** of non-null validation statuses are rejected/duplicate. All scoring uses `approved` records only.
- PPI top-1 (clean): **Btp051 - Safina Plaza Junction**, 27.3 validated violations/day.
- Forecast **MAE 11.40** on Mar 2024 validation set — beats 7-day rolling baseline (12.33), near-tie with yesterday's count (11.06).
- PPI ±10% weight sensitivity: **STABLE** (14–15/15 top-15 overlap across all perturbations).

---

## Hugging Face Deployment

The `src/dashboard/` folder is deployed as a standalone Spaces app. The precomputed Parquet artifacts (`data/processed/`) are committed to the Space repository since the raw CSV (300 MB) is not re-runnable in the Spaces environment.

See [`src/dashboard/README_HF.md`](src/dashboard/README_HF.md) for Space-specific setup.

---

## Known Limitations (stated, not hidden)

1. **PPI is a proxy** — no speed/volume data; cannot measure actual traffic-flow impact.
2. **`created_datetime` = enforcement-action time**, not offense-occurrence time.
3. Forecast reliable only for top-volume junctions with ≥30 days history; long-tail excluded.
4. No real-time feed — historical intelligence system only.
