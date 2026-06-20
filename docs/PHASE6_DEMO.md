# Phase 6 — Demo Narrative & Hard-Question Answers
**ParkPulse · PS1 · Flipkart GRID**
Last updated: 2026-06-21

---

## 90-Second Demo Narrative

**[0–15s] Open with the real data finding, not the slide**
> "Before we built anything, we profiled both available datasets.
> PS1 had 298,450 records, zero nulls on every field we needed,
> and one finding that most teams will miss: the timestamps are UTC.
> Convert to IST and the 'peak violation hour' shifts from midnight
> to 10 AM — which is actually consistent with morning enforcement
> sweeps, not with when people park illegally.
> We treat every time-based chart as enforcement-action time and say so.
> That distinction matters if a judge asks why violations peak at 10 AM."

**[15–40s] Overview → map → top hotspot**
> "This is the live dashboard. Every number here comes from
> 115,400 validated records — we filtered to 'approved' status only,
> which removes the 28.9% rejected or duplicate tags.
> The map shows 164 named junctions ranked by PPI — Parking Pressure Index —
> a composite score we built from frequency, severity, repeat offenders,
> and persistence. Circle size is violations per day. Color is tier.
> One thing we want to flag: 147,880 records — 49.5% of the dataset —
> carried no usable junction name. We don't drop them; they still feed
> the geographic DBSCAN clustering. But they're excluded from the named
> ranking, and we say exactly why on the Methodology page."
> [Click Safina Plaza Junction]

**[40–55s] Hotspot Detail**
> "This is Safina Plaza — top-ranked, 27 validated violations per day,
> Critical tier. The PPI breakdown shows why: frequency drives 0.40
> of its score, persistence 0.10. Enforcement peaks between 9 and 11 AM IST
> — that's the morning sweep window, not a random artifact.
> Below is the forecast: LightGBM trained on Nov–Feb, validated on March.
> MAE of 11.4 violations per day. It beats the 7-day rolling baseline
> by about one violation per day. We show the number whatever it comes out to —
> we didn't tune until it looked good."

**[55–75s] Patrol Allocation**
> [Switch to Patrol Allocation, set slider to 10]
> "Given 10 patrol units, the MILP distributes them in under a second —
> three to Safina Plaza, capped at five per hotspot so we don't
> pile everything onto one location. Critical-tier junctions
> are guaranteed at least one unit. This is linear programming,
> not reinforcement learning — RL would need observed outcomes
> from past deployments, which we don't have yet. We say that explicitly."

**[75–90s] Close**
> "The full pipeline — clean, cluster, PPI, forecast, allocate —
> runs end-to-end in under 20 seconds from raw CSV.
> Everything precomputed before the demo; dashboard loads in under 2 seconds.
> The one thing we'd add with more time is a live traffic-flow API feed
> to replace the PPI proxy with a measured impact number.
> That's Phase 2, and it's in the docs."

---

## Hard Questions — Prepared Answers

### "How do you know the PPI weights are right?"
We don't claim they're optimal — we claim they're **transparent and stable**.
The weights (0.4 / 0.3 / 0.2 / 0.1) are published in config.py and on the
Methodology page. We ran a ±10% sensitivity check: perturb each weight,
renormalize, recompute — the top-15 ranking overlaps 14–15/15 in every case.
That means the ranking is robust to reasonable weight changes.
If you disagree with the weights, change them in one place (config.py)
and rerun. That's the point of centralizing them.

### "What if the model is overfit?"
The model was trained on Nov 2023–Feb 2024, early-stopping on Mar 2024 validation.
The Apr 2024 slice was empty after the approved-only filter (partial month,
zero validated rows), so we report Mar 2024 validation metrics honestly —
MAE 11.40, RMSE 15.62, WAPE 94.6%. It beats the 7-day rolling baseline (12.33)
but not yesterday's count (11.06). We show both comparisons. The high WAPE
reflects low-volume junctions where small absolute errors become large percentages
— we state that rather than hiding it. The validation split is genuinely
held-out from training (LightGBM saw it only for early stopping, not for
weight updates after the stop).

### "Why no RL / GNN / Digital Twin?"
RL needs a reward signal — specifically, observed effects of past deployments
on subsequent violation counts. That data doesn't exist in this dataset.
We'd need to run real deployments, record outcomes, and collect that feedback
before training a policy. Claiming RL without that is fabricating a label.
A MILP is fully legitimate, runs in milliseconds, and is completely explainable
to the officer reading the output. Same reasoning applies to GNNs and digital twins —
they'd need graph-structured or simulation-validated ground truth we don't have.
This is in PRD §5 Non-Goals, and the answer is the same every time someone
suggests adding one: "what labeled outcome data would that need, and do we have it?"

### "How do you know 'No Junction' isn't a real place?"
It's a literal placeholder value present in 147,880 records across 54 different
police stations and every quadrant of Bangalore's bounding box. Its mean lat/long
lands near the geographic center of the city — it's the average of thousands of
scattered points, not a real location. We confirmed this by checking the
geographic spread of its records (they span the entire dataset extent)
and by looking at the raw data — the field was simply blank at entry time,
coerced to the string "No Junction" by the recording system.

### "Why does the model only beat one of the two baselines?"
The 7-day rolling average is a relatively strong baseline for daily count series
with slow trends — beating it by any margin is meaningful. Yesterday's count
is extremely hard to beat for short-horizon forecasts because day-to-day
autocorrelation is high. A MAE of 11.40 vs 11.06 for yesterday is a near-tie,
not a meaningful gap in either direction. The honest position is: the model
adds value over a simple rolling average, and roughly matches yesterday's count.
For a prototype with three months of training data per junction, that's the
expected range. We'd expect the gap to widen with more data and richer features
(e.g., local event calendars, weather).

### "What would you do with more time?"
Exactly what's in PRD §9:
1. Integrate a live traffic-flow/speed API so PPI uses measured impact,
   not a proxy built from violation counts.
2. Add a CV/OCR layer once image data is available, to auto-validate
   violations and reduce the 28.9% rejection rate.
3. Move from static MILP to continuous RL once post-deployment outcome
   data (did violations actually drop after a patrol?) is collected.
None of those are improvised — they're in the docs and they each have a
specific prerequisite that isn't met by the current dataset.

---

## Pre-Demo Freeze Checklist
- [ ] Run `python -m src.pipeline.run_all` from clean state — confirm completes in <30s
- [ ] Run `python _final_verify.py` — confirm 17/17 PASS
- [ ] Open dashboard at localhost:8505, click through all 4 pages
- [ ] Verify top-5 cards all show name + PPI + tier + violations/day + why
- [ ] Verify Safina Plaza Detail: PPI bars visible with values, hourly chart caption readable
- [ ] Verify Allocation with 10 units: map shows numbered markers, table shows 3 units to Safina
- [ ] Verify Methodology page: attribution finding callout visible, backtest numbers present
- [ ] Do not regenerate artifacts after this point
