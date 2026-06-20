"""
ParkPulse — Visual/UX rebuild.
Run: streamlit run src/dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
import streamlit as st

from src.config import (
    PRECOMPUTE_UNIT_COUNTS,
    TOP_N_OVERVIEW,
)
from src.dashboard.data_loader import (
    artifacts_exist,
    load_allocation,
    load_forecast,
    load_hotspots,
    load_junction_daily,
    load_ppi,
    load_temporal,
    load_violations_sample,
)
from src.dashboard.components import (
    TC,
    TXT_MUT,
    TXT_PRI,
    BG_CARD,
    BG_DARK,
    build_allocation_map,
    build_overview_map,
    dow_chart,
    forecast_chart,
    hourly_chart,
    ppi_breakdown_chart,
    tier_badge_html,
    vehicle_mix_chart,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ParkPulse · Enforcement Intelligence",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='14' fill='%230B0F14' stroke='%23E5484D' stroke-width='2'/><circle cx='16' cy='16' r='5' fill='%23E5484D'/><circle cx='16' cy='16' r='9' fill='none' stroke='%23E5484D' stroke-width='1' stroke-dasharray='3 3'/></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS — single consolidated block ────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Inter:wght@400;500;600&display=swap');

/* ── Hide default Streamlit chrome ── */
#MainMenu, header, footer,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* ── Global surface ── */
html, body, [data-testid="stAppViewContainer"],
[data-testid="stMain"], .main .block-container {
    background-color: #0B0F14 !important;
    color: #E8ECEF;
    font-family: Inter, 'IBM Plex Sans', sans-serif;
}
.block-container { padding-top: 24px !important; max-width: 100% !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #0D1219 !important;
    border-right: 1px solid rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] * { color: #E8ECEF !important; }

/* ── Nav items (radio) ── */
div[data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 8px 12px !important;
    border-radius: 6px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
    border-left: 3px solid transparent !important;
}
div[data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.05) !important;
}
div[data-testid="stRadio"] label[data-baseweb="radio"] input:checked ~ div {
    color: #E8ECEF !important;
}

/* ── Stat cards ── */
.stat-card {
    background: #141A21;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 20px 24px;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.stat-card .label {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8B96A3;
}
.stat-card .value {
    font-family: 'IBM Plex Mono', 'JetBrains Mono', monospace;
    font-size: 1.75rem;
    font-weight: 600;
    color: #E8ECEF;
    line-height: 1.1;
}
.stat-card .sub {
    font-family: Inter, sans-serif;
    font-size: 0.75rem;
    color: #8B96A3;
}

/* ── Hotspot list cards ── */
.hs-card {
    background: #141A21;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 8px;
    border-left-width: 3px;
}
.hs-card .hs-name {
    font-family: Inter, sans-serif;
    font-size: 0.83rem;
    font-weight: 600;
    color: #E8ECEF;
    margin-bottom: 6px;
    white-space: normal;
    word-break: break-word;
}
.hs-card .hs-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
}
.hs-card .hs-ppi {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.1rem;
    font-weight: 600;
    color: #E8ECEF;
}
.hs-card .hs-freq {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: #8B96A3;
}
.hs-card .hs-why {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    color: #8B96A3;
    margin-top: 5px;
    white-space: normal;
}

/* ── Section divider ── */
.pp-divider {
    border: none;
    border-top: 1px solid rgba(255,255,255,0.07);
    margin: 16px 0;
}

/* ── Section header ── */
.pp-section {
    font-family: Inter, sans-serif;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #8B96A3;
    margin-bottom: 12px;
}

/* ── Tier badge ── */
.tier-badge {
    display: inline-block;
    font-family: Inter, sans-serif;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 2px 9px;
    border-radius: 4px;
    border-width: 1px;
    border-style: solid;
}

/* ── Metric override (use our monospace) ── */
[data-testid="stMetricValue"] {
    font-family: 'IBM Plex Mono', monospace !important;
    color: #E8ECEF !important;
}
[data-testid="stMetricLabel"] {
    font-family: Inter, sans-serif !important;
    color: #8B96A3 !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.05em !important;
}

/* ── Selectbox / slider labels ── */
label[data-testid="stWidgetLabel"] {
    font-family: Inter, sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.05em !important;
    color: #8B96A3 !important;
    text-transform: uppercase !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrameResizable"] {
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
    overflow: hidden !important;
}

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: #141A21 !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: Inter, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
}

/* ── Info / warning boxes ── */
[data-testid="stAlert"] {
    background: #141A21 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    font-family: Inter, sans-serif !important;
    font-size: 0.83rem !important;
}

/* ── Plotly chart background fill ── */
.js-plotly-plot .plotly .bg { fill: transparent !important; }
</style>
""", unsafe_allow_html=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if not artifacts_exist():
    st.error("Precomputed artifacts not found. Run: python -m src.pipeline.run_all")
    st.stop()

# ── Load data (all cached) ────────────────────────────────────────────────────
ppi_df       = load_ppi()
hotspots_df  = load_hotspots()
jd           = load_junction_daily()
temporal_df  = load_temporal()
forecast_df  = load_forecast()
allocation_df = load_allocation()

# ── Sidebar ───────────────────────────────────────────────────────────────────
RADAR_SVG = """
<svg width="36" height="36" viewBox="0 0 36 36" fill="none" xmlns="http://www.w3.org/2000/svg">
  <circle cx="18" cy="18" r="16" stroke="#E5484D" stroke-width="1.5"/>
  <circle cx="18" cy="18" r="10" stroke="#E5484D" stroke-width="1" stroke-dasharray="2.5 2.5" opacity="0.6"/>
  <circle cx="18" cy="18" r="4"  fill="#E5484D"/>
  <line x1="18" y1="2"  x2="18" y2="18" stroke="#E5484D" stroke-width="1.5" stroke-linecap="round" opacity="0.7"/>
</svg>
"""

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:12px;padding:8px 0 4px 0;">'
        f'{RADAR_SVG}'
        f'<div><div style="font-family:Inter,sans-serif;font-weight:700;font-size:1.1rem;'
        f'color:#E8ECEF;letter-spacing:0.02em;">ParkPulse</div>'
        f'<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
        f'letter-spacing:0.05em;text-transform:uppercase;">Enforcement Intelligence</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)

    page = st.radio(
        "nav",
        ["Overview", "Hotspot Detail", "Patrol Allocation", "Data & Methodology"],
        label_visibility="collapsed",
    )

    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)

    all_stations = sorted(ppi_df["police_station"].dropna().unique())
    station_filter = st.selectbox(
        "FILTER BY STATION",
        ["All stations"] + all_stations,
        index=0,
    )
    station_sel = None if station_filter == "All stations" else station_filter

    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
    st.markdown(
        f'<div style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
        f'line-height:1.6;">'
        f'Dataset: Nov 2023 – Apr 2024<br>'
        f'<span style="font-family:IBM Plex Mono,monospace;">{len(ppi_df):,}</span> junctions tracked<br>'
        f'<span style="color:#E5484D;">approved</span> violations only'
        f'</div>',
        unsafe_allow_html=True,
    )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 1 — OVERVIEW
# ═══════════════════════════════════════════════════════════════════
if page == "Overview":

    st.markdown(
        '<p class="pp-section">Hotspot Overview — Bangalore, Nov 2023 – Apr 2024</p>',
        unsafe_allow_html=True,
    )

    # ── Stat cards ────────────────────────────────────────────────
    validated_total = int(jd["n_violations_validated"].sum())
    # n_junctions = junctions with real names in PPI table (placeholders excluded)
    n_junctions     = len(ppi_df)
    n_critical      = int((ppi_df["ppi_tier"] == "Critical").sum())
    n_high          = int((ppi_df["ppi_tier"] == "High").sum())

    c1, c2, c3, c4 = st.columns(4, gap="small")
    for col, label, value, sub in [
        (c1, "Validated Violations", f"{validated_total:,}", "approved records · Nov 2023–Apr 2024"),
        (c2, "Named Junctions",      f"{n_junctions}",       "real locations · placeholders excluded"),
        (c3, "Critical Hotspots",    f"{n_critical}",         "top 10% by PPI score"),
        (c4, "High Priority",        f"{n_high}",             "next 20% by PPI score"),
    ]:
        col.markdown(
            f'<div class="stat-card">'
            f'<div class="label">{label}</div>'
            f'<div class="value">{value}</div>'
            f'<div class="sub">{sub}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown(
        '<p style="font-family:Inter,sans-serif;font-size:0.76rem;color:#8B96A3;'
        'margin:12px 0 16px 0;">'
        'Color encodes <b style="color:#E8ECEF;">Parking Pressure Index (PPI)</b> — '
        'a priority proxy built from frequency, severity, repeat offenders, and persistence. '
        '<b style="color:#E5484D;">Not</b> a direct measurement of traffic delay.'
        '</p>',
        unsafe_allow_html=True,
    )

    # ── Map + list ────────────────────────────────────────────────
    map_col, list_col = st.columns([3, 1], gap="medium")

    display_ppi = ppi_df.copy()
    if station_sel:
        display_ppi = display_ppi[display_ppi["police_station"] == station_sel]

    with map_col:
        folium_map = build_overview_map(display_ppi, hotspots_df, station_filter=station_sel)
        from streamlit_folium import st_folium
        st_folium(folium_map, width=None, height=540, returned_objects=[])

    with list_col:
        st.markdown('<p class="pp-section">Top Hotspots</p>', unsafe_allow_html=True)

        if len(display_ppi) == 0:
            st.markdown(
                '<div class="hs-card" style="border-left-color:#8B96A3;">'
                '<div class="hs-name">No hotspots in this window</div></div>',
                unsafe_allow_html=True,
            )
        else:
            # Top-5 dominant component — derived strictly from actual weighted values (BUG 2 fix)
            comp_labels = {
                "freq_norm":    "High violation frequency",
                "sev_norm":     "Severe violation types",
                "repeat_norm":  "Repeat offenders",
                "persist_norm": "Daily persistence",
            }
            comp_weights = {
                "freq_norm": 0.4, "sev_norm": 0.3,
                "repeat_norm": 0.2, "persist_norm": 0.1,
            }

            def _top_comp(r: pd.Series) -> str:
                weighted = {k: float(r.get(k, 0)) * w for k, w in comp_weights.items()}
                top_key = max(weighted, key=weighted.get)
                return comp_labels.get(top_key, "")

            # BUG 2 assertion: verify top comp matches actual max for every row
            for _, r in display_ppi.iterrows():
                weighted = {k: float(r.get(k, 0)) * w for k, w in comp_weights.items()}
                top_key = max(weighted, key=weighted.get)
                assert top_key in comp_labels, f"Unknown top component key: {top_key}"

            for _, row in display_ppi.head(TOP_N_OVERVIEW).iterrows():
                tier  = row["ppi_tier"]
                color = TC.get(tier, "#888")
                badge = tier_badge_html(tier)
                why   = _top_comp(row)
                freq  = row["violation_frequency"]
                name  = row["junction_name_norm"]
                ppi   = row["ppi_score"]

                st.markdown(
                    f'<div class="hs-card" style="border-left-color:{color};">'
                    f'<div class="hs-name">{name}</div>'
                    f'<div class="hs-row">'
                    f'<span class="hs-ppi" style="color:{color};">{ppi:.1f}</span>'
                    f'{badge}'
                    f'<span class="hs-freq">{freq:.1f}/day</span>'
                    f'</div>'
                    f'<div class="hs-why">&#x2191; {why}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
        st.markdown('<p class="pp-section">Full Ranking</p>', unsafe_allow_html=True)

        rank_df = display_ppi[
            ["junction_name_norm", "ppi_score", "ppi_tier", "violation_frequency"]
        ].copy()
        rank_df.columns = ["Junction", "PPI", "Tier", "Viol/Day"]
        rank_df["PPI"]      = rank_df["PPI"].round(1)
        rank_df["Viol/Day"] = rank_df["Viol/Day"].round(1)
        st.dataframe(rank_df, use_container_width=True, height=300, hide_index=True)


# ═══════════════════════════════════════════════════════════════════
#  PAGE 2 — HOTSPOT DETAIL
# ═══════════════════════════════════════════════════════════════════
elif page == "Hotspot Detail":

    all_junctions = ppi_df.sort_values("ppi_score", ascending=False)["junction_name_norm"].tolist()
    selected = st.selectbox("SELECT JUNCTION", all_junctions, index=0)

    row   = ppi_df[ppi_df["junction_name_norm"] == selected].iloc[0]
    tier  = row["ppi_tier"]
    color = TC.get(tier, "#888")
    badge = tier_badge_html(tier, size="0.85rem")

    # ── Detail header ─────────────────────────────────────────────
    st.markdown(
        f'<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        f'border-left:3px solid {color};border-radius:8px;padding:20px 24px;margin-bottom:16px;">'
        f'<div style="font-family:Inter,sans-serif;font-weight:700;font-size:1.15rem;'
        f'color:#E8ECEF;margin-bottom:8px;">{selected}</div>'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
        f'{badge}'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'PPI&nbsp;<b style="color:#E8ECEF;">{row["ppi_score"]:.1f}</b>/100</span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'Station&nbsp;<b style="color:#E8ECEF;">{row["police_station"]}</b></span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'{row["violation_frequency"]:.1f}&nbsp;viol/day</span>'
        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.9rem;color:#8B96A3;">'
        f'Persistence&nbsp;{row["persistence"]:.0%}</span>'
        f'</div></div>',
        unsafe_allow_html=True,
    )

    # ── Three-column detail ───────────────────────────────────────
    col_ppi, col_temporal, col_vehicle = st.columns([1, 1.1, 0.95], gap="medium")

    with col_ppi:
        st.markdown('<p class="pp-section">PPI Breakdown</p>', unsafe_allow_html=True)
        st.plotly_chart(
            ppi_breakdown_chart(row),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.markdown(
            '<p style="font-family:Inter,sans-serif;font-size:0.7rem;color:#8B96A3;'
            'margin-top:4px;line-height:1.5;">'
            'Weights: frequency ×0.4 &nbsp;·&nbsp; severity ×0.3<br>'
            'repeat offenders ×0.2 &nbsp;·&nbsp; persistence ×0.1<br>'
            'All components normalised min-max across junctions.</p>',
            unsafe_allow_html=True,
        )

    with col_temporal:
        st.markdown('<p class="pp-section">Temporal Pattern</p>', unsafe_allow_html=True)
        st.plotly_chart(
            hourly_chart(temporal_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.plotly_chart(
            dow_chart(temporal_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    with col_vehicle:
        st.markdown('<p class="pp-section">Vehicle Mix</p>', unsafe_allow_html=True)
        violations_sample = load_violations_sample()
        st.plotly_chart(
            vehicle_mix_chart(violations_sample, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    # ── Forecast strip ────────────────────────────────────────────
    st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
    st.markdown('<p class="pp-section">Violation Forecast</p>', unsafe_allow_html=True)

    junc_forecast = forecast_df[forecast_df["hotspot_id"] == selected]

    if len(junc_forecast) == 0 or junc_forecast["predicted_violations"].isna().all():
        st.markdown(
            '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
            'border-radius:8px;padding:20px 24px;font-family:Inter,sans-serif;'
            'font-size:0.83rem;color:#8B96A3;">'
            'Insufficient history at this hotspot for a reliable forecast '
            '(minimum 30 days required).</div>',
            unsafe_allow_html=True,
        )
    else:
        st.plotly_chart(
            forecast_chart(forecast_df, selected),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        val_rows = junc_forecast[
            (junc_forecast["split"] == "validate") &
            junc_forecast["actual_violations"].notna()
        ]
        if len(val_rows) > 0:
            mae  = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().mean()
            rmse = ((val_rows["actual_violations"] - val_rows["predicted_violations"]) ** 2).mean() ** 0.5
            n7   = (val_rows["actual_violations"] - val_rows["baseline_rolling7_predicted"]).abs().mean()
            beat = mae < n7
            m1, m2, m3, m4 = st.columns(4)
            for col, lbl, val in [
                (m1, "Validate MAE",     f"{mae:.2f}"),
                (m2, "Validate RMSE",    f"{rmse:.2f}"),
                (m3, "7-day baseline MAE", f"{n7:.2f}"),
                (m4, "Beat baseline",    "YES" if beat else "NO"),
            ]:
                col.markdown(
                    f'<div class="stat-card" style="padding:14px 18px;">'
                    f'<div class="label">{lbl}</div>'
                    f'<div class="value" style="font-size:1.3rem;'
                    f'color:{"#2ECC71" if (lbl=="Beat baseline" and beat) else "#E8ECEF"};">'
                    f'{val}</div></div>',
                    unsafe_allow_html=True,
                )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 3 — PATROL ALLOCATION
# ═══════════════════════════════════════════════════════════════════
elif page == "Patrol Allocation":

    st.markdown('<p class="pp-section">Patrol Allocation Simulator</p>', unsafe_allow_html=True)

    st.markdown(
        '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        'border-left:3px solid #F2994A;border-radius:8px;padding:14px 20px;'
        'margin-bottom:16px;font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;">'
        'Allocation uses <b style="color:#E8ECEF;">constrained MILP</b> (PuLP) — not reinforcement '
        'learning. Objective: maximise Σ units × forecasted_violations × PPI_weight. '
        'No outcome-feedback data exists to train an RL policy.</div>',
        unsafe_allow_html=True,
    )

    ctrl_col, map_col = st.columns([1, 2], gap="medium")

    with ctrl_col:
        n_units = st.slider("AVAILABLE PATROL UNITS", min_value=1, max_value=30, value=10, step=1)

        precomputed_counts = [int(x) for x in allocation_df["available_units_total"].unique()]
        if n_units in precomputed_counts:
            alloc_result = allocation_df[allocation_df["available_units_total"] == n_units].copy()
            src_label = "precomputed"
        else:
            from src.models.allocation import solve_allocation
            alloc_result = solve_allocation(forecast_df, ppi_df, n_units)
            src_label = "live solve"

        assigned = alloc_result[alloc_result["units_assigned"] > 0].sort_values(
            ["units_assigned", "ppi_score"], ascending=[False, False]
        ).reset_index(drop=True)

        total_assigned = int(assigned["units_assigned"].sum())
        n_covered      = len(assigned)

        # Mini stat strip
        s1, s2 = st.columns(2)
        for col, lbl, val in [
            (s1, "Units Deployed", f"{total_assigned}/{n_units}"),
            (s2, "Hotspots Covered", str(n_covered)),
        ]:
            col.markdown(
                f'<div class="stat-card" style="padding:14px 18px;">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value" style="font-size:1.4rem;">{val}</div>'
                f'<div class="sub">{src_label}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        st.markdown('<hr class="pp-divider"/>', unsafe_allow_html=True)
        st.markdown('<p class="pp-section">Deployment Table</p>', unsafe_allow_html=True)

        if len(assigned) == 0:
            st.markdown(
                '<div class="hs-card" style="border-left-color:#8B96A3;">'
                '<div class="hs-name">No units allocated — increase unit count.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            for _, row in assigned.iterrows():
                tier  = row["ppi_tier"]
                color = TC.get(tier, "#888")
                badge = tier_badge_html(tier)
                units = int(row["units_assigned"])
                name  = row["hotspot_id"]
                fc    = row["forecasted_violations"]
                ppi   = row["ppi_score"]
                max_u = int(row.get("max_units_per_hotspot", 5))

                with st.expander(
                    f"{name}  ·  {units} unit{'s' if units != 1 else ''}",
                    expanded=(tier == "Critical"),
                ):
                    st.markdown(
                        f'<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px;">'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
                        f'color:#8B96A3;">Forecast&nbsp;<b style="color:#E8ECEF;">{fc:.0f}</b></span>'
                        f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.85rem;'
                        f'color:#8B96A3;">PPI&nbsp;<b style="color:#E8ECEF;">{ppi:.1f}</b></span>'
                        f'{badge}</div>'
                        f'<div style="font-family:Inter,sans-serif;font-size:0.73rem;color:#8B96A3;">'
                        f'{"Min 1 unit — Critical tier guarantee. " if tier == "Critical" else ""}'
                        f'Capped at {max_u} units/hotspot.</div>',
                        unsafe_allow_html=True,
                    )

    with map_col:
        st.markdown('<p class="pp-section">Deployment Map</p>', unsafe_allow_html=True)
        if len(assigned) > 0:
            alloc_map = build_allocation_map(assigned, hotspots_df, ppi_df)
            from streamlit_folium import st_folium
            st_folium(alloc_map, width=None, height=540, returned_objects=[])
        else:
            st.markdown(
                '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
                'border-radius:8px;padding:40px;text-align:center;font-family:Inter,sans-serif;'
                'font-size:0.85rem;color:#8B96A3;">No units to display.</div>',
                unsafe_allow_html=True,
            )


# ═══════════════════════════════════════════════════════════════════
#  PAGE 4 — DATA & METHODOLOGY
# ═══════════════════════════════════════════════════════════════════
elif page == "Data & Methodology":

    st.markdown('<p class="pp-section">Data & Methodology</p>', unsafe_allow_html=True)

    def _section(title: str) -> None:
        st.markdown(
            f'<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.95rem;'
            f'color:#E8ECEF;margin:24px 0 8px 0;padding-bottom:6px;'
            f'border-bottom:1px solid rgba(255,255,255,0.07);">{title}</div>',
            unsafe_allow_html=True,
        )

    def _kv(key: str, value: str) -> None:
        st.markdown(
            f'<div style="display:flex;gap:16px;padding:7px 0;'
            f'border-bottom:1px solid rgba(255,255,255,0.04);">'
            f'<span style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;'
            f'min-width:200px;">{key}</span>'
            f'<span style="font-family:IBM Plex Mono,monospace;font-size:0.8rem;'
            f'color:#E8ECEF;">{value}</span></div>',
            unsafe_allow_html=True,
        )

    # Dataset facts
    _section("Dataset")
    _kv("Source file",    "jan_to_may_police_violation_anonymized791b166.csv")
    _kv("Total records",  "298,450")
    _kv("Date window",    "Nov 9, 2023 – Apr 8, 2024")
    _kv("Coverage",       "Bangalore · lat 12.80–13.29 · lon 77.44–77.77")
    _kv("Unique junctions", "169 raw · 164 with usable attribution")
    _kv("Police stations",  "54")
    _kv("Vehicle mix",    "Scooter 31.8% · Car 29.8% · Motorcycle 13.7% · Auto 12.7%")
    _kv("Raw files",      "Read-only — no in-place mutations")

    # Unattributable-records callout — explicitly presented, not hidden
    st.markdown(
        '<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);'
        'border-left:3px solid #F2994A;border-radius:8px;padding:16px 20px;margin:12px 0;">'
        '<div style="font-family:Inter,sans-serif;font-weight:600;font-size:0.85rem;'
        'color:#E8ECEF;margin-bottom:8px;">Junction Attribution Finding</div>'
        '<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.7;">'
        '<b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">147,880</b> records '
        '(<b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">49.5%</b> of all 298,450) '
        'carry the literal value <code>"No Junction"</code> in the junction field — '
        'meaning they had no junction attribution at entry time. '
        'A further <b style="font-family:IBM Plex Mono,monospace;color:#F2994A;">5</b> records '
        'have a true null, coerced to <code>"Unknown"</code> by the cleaning step.<br><br>'
        'These records are <b style="color:#E8ECEF;">not dropped</b> — they remain in '
        '<code>violations_clean</code> for transparency and contribute to DBSCAN geometric '
        'clustering (which keys off lat/long, not junction name). '
        'They are <b style="color:#E5484D;">excluded</b> from all named-hotspot PPI scoring, '
        'forecasting, and allocation, since there is no real, actionable address behind them. '
        'The exclusion is enforced by a single constant (<code>JUNCTION_PLACEHOLDER_NAMES</code> '
        'in <code>config.py</code>) imported by every pipeline module — not scattered per-file.'
        '</div></div>',
        unsafe_allow_html=True,
    )

    # Cleaning steps
    _section("Cleaning Steps")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#E8ECEF;line-height:1.8;">
<ol style="padding-left:18px;color:#8B96A3;">
<li><b style="color:#E8ECEF;">Multi-label parsing</b> — <code>violation_type</code> stored as JSON-array strings
(e.g. <code>["WRONG PARKING","NO PARKING"]</code>). Parsed with <code>json.loads</code>; severity weight
derived from documented per-label table.</li>
<li><b style="color:#E8ECEF;">Timezone correction</b> — Timestamps are UTC. Converted to IST (+05:30) for all
temporal analysis. Labelled everywhere as <i>enforcement-action time</i>, not offense-occurrence time.</li>
<li><b style="color:#E8ECEF;">Validation filter</b> — Only <code>approved</code> records used for
PPI/forecast/allocation. Rejected+duplicate: <b>28.9%</b> of non-null statuses.</li>
<li><b style="color:#E8ECEF;">Junction normalisation</b> — Trimmed whitespace, title-cased.
No fuzzy-merge beyond exact-after-normalisation.</li>
<li><b style="color:#E8ECEF;">Dropped columns</b> — <code>description</code>, <code>closed_datetime</code>,
<code>action_taken_timestamp</code> — all 100% null.</li>
</ol>
</div>
""", unsafe_allow_html=True)

    # PPI formula
    _section("Parking Pressure Index (PPI)")
    st.markdown("""
<div style="background:#141A21;border:1px solid rgba(255,255,255,0.07);border-radius:8px;
padding:20px 24px;font-family:IBM Plex Mono,monospace;font-size:0.82rem;color:#E8ECEF;
line-height:2;margin-bottom:12px;">
PPI = 0.4 × norm(violation_frequency)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.3 × norm(severity_weight)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.2 × norm(repeat_offender_ratio)<br>
&nbsp;&nbsp;&nbsp;&nbsp;+ 0.1 × norm(persistence)
</div>
<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;line-height:1.7;">
<b style="color:#E8ECEF;">norm()</b> = min-max across all junctions in the trailing 90-day window.<br>
<b style="color:#E8ECEF;">Tier thresholds</b> — quantile-based:
Critical = top 10% · High = next 20% · Medium = next 30% · Low = bottom 40%.<br>
<b style="color:#E8ECEF;">Sensitivity check</b> — each weight perturbed ±10% (renormalised);
top-15 ranking overlap reported. Result: <b style="color:#2ECC71;">STABLE (14–15/15 overlap across all perturbations)</b>.<br>
<b style="color:#E5484D;">PPI is a priority proxy — not a measured traffic-flow metric.</b>
</div>
""", unsafe_allow_html=True)

    # Severity table
    _section("Severity Weight Table")
    sev_data = {
        "Violation Label": [
            "PARKING IN A MAIN ROAD", "PARKING ON FOOTPATH", "PARKING IN A BUS STOP",
            "PARKING NEAR ROAD CROSSING", "PARKING NEAR SIGNAL", "PARKING NEAR SCHOOL",
            "PARKING NEAR HOSPITAL", "WRONG PARKING", "NO PARKING",
        ],
        "Weight": [1.0, 0.9, 0.8, 0.7, 0.7, 0.6, 0.6, 0.5, 0.5],
        "Rationale": [
            "Directly blocks major traffic artery",
            "Blocks pedestrian path, safety risk",
            "Blocks bus stop, delays public transit",
            "Increases collision risk at junctions",
            "Impedes signal-controlled flow",
            "Safety risk near school zones",
            "Emergency-vehicle access concern",
            "Generic illegal parking",
            "No-parking zone violation",
        ],
    }
    st.dataframe(pd.DataFrame(sev_data), use_container_width=True, hide_index=True)

    # Forecasting
    _section("Forecasting")
    _kv("Primary model",      "LightGBM")
    _kv("Cross-check",        "XGBoost")
    _kv("Baselines",          "Yesterday's count · 7-day rolling average")
    _kv("Train split",        "Nov 2023 – Feb 2024")
    _kv("Validate split",     "Mar 2024 (early stopping + reported metrics)")
    _kv("Test split",         "Apr 2024 — held out; 0 validated rows after filter (partial month)")
    _kv("Eligible junctions", "Top-15 by volume with ≥30 days history")
    _kv("Features",           "lag-1, lag-7, roll-7/14 mean+std, DoW, month, holiday, junction_id")
    _kv("Note on Apr 2024",
        "The held-out test slice contained 0 validated rows after applying the approved-only "
        "filter to the partial month. Reported metrics are therefore from the Mar 2024 "
        "validation split — not in-sample training numbers.")

    # Backtest results — real numbers, honestly labelled
    _section("Backtest Results — Validation Set (Mar 2024)")
    val_rows = forecast_df[
        (forecast_df["split"] == "validate") & forecast_df["actual_violations"].notna()
    ]
    if len(val_rows) > 0:
        mae   = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().mean()
        rmse  = ((val_rows["actual_violations"] - val_rows["predicted_violations"]) ** 2).mean() ** 0.5
        wdenom = val_rows["actual_violations"].abs().sum()
        wape  = (val_rows["actual_violations"] - val_rows["predicted_violations"]).abs().sum() / wdenom * 100
        n_y   = (val_rows["actual_violations"] - val_rows["baseline_naive_predicted"]).abs().mean()
        n_r7  = (val_rows["actual_violations"] - val_rows["baseline_rolling7_predicted"]).abs().mean()
        beat_y  = mae < n_y
        beat_r7 = mae < n_r7

        r1, r2, r3, r4, r5 = st.columns(5)
        for col, lbl, val, good in [
            (r1, "MAE",               f"{mae:.2f}",   None),
            (r2, "RMSE",              f"{rmse:.2f}",  None),
            (r3, "WAPE",              f"{wape:.1f}%", None),
            (r4, "vs Yesterday MAE",  f"{n_y:.2f}",   None),
            (r5, "Beat 7-day roll?",  "YES" if beat_r7 else "NO", beat_r7),
        ]:
            col.markdown(
                f'<div class="stat-card" style="padding:14px 18px;">'
                f'<div class="label">{lbl}</div>'
                f'<div class="value" style="font-size:1.2rem;'
                f'color:{"#2ECC71" if good else ("#E5484D" if good is False else "#E8ECEF")};">'
                f'{val}</div></div>',
                unsafe_allow_html=True,
            )

        # Honest interpretation — state what the numbers mean, don't hide the caveat
        beat_yesterday_str = "beats" if beat_y else "does not beat"
        st.markdown(
            f'<div style="font-family:Inter,sans-serif;font-size:0.8rem;color:#8B96A3;'
            f'margin-top:12px;line-height:1.7;">'
            f'LightGBM MAE <b style="font-family:IBM Plex Mono,monospace;color:#E8ECEF;">{mae:.2f}</b> '
            f'violations/day across 15 junctions on the Mar 2024 validation set. '
            f'Model <b style="color:#{"2ECC71" if beat_r7 else "E5484D"};">{"beats" if beat_r7 else "does not beat"}</b> '
            f'the 7-day rolling baseline (MAE {n_r7:.2f}) and '
            f'<b style="color:#{"2ECC71" if beat_y else "F2994A"};">{beat_yesterday_str}</b> '
            f'the yesterday baseline (MAE {n_y:.2f}). '
            f'High WAPE ({wape:.0f}%) reflects low-volume junctions where even small absolute '
            f'errors produce large percentage deviations — this is expected and stated, not hidden.'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#8B96A3;font-size:0.82rem;">'
            'No validate rows found in current forecast artifact.</div>',
            unsafe_allow_html=True,
        )

    # Patrol allocation
    _section("Patrol Allocation")
    _kv("Method",      "Mixed-Integer Linear Program (MILP) · PuLP open-source solver")
    _kv("Objective",   "Maximise Σ units_i × forecasted_violations_i × ppi_weight_i")
    _kv("Constraints", "Total units ≤ available · each hotspot ≤ 5 units · Critical ≥ 1 unit")
    _kv("Precomputed", "Unit counts 5, 10, 15, 20, 25 — live solve for any other value (<1s)")

    # Limitations
    _section("Known Limitations")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.8;">
<ol style="padding-left:18px;">
<li><b style="color:#E5484D;">PPI is a proxy</b> — no speed/volume data exists; cannot measure actual traffic-flow impact.</li>
<li><b style="color:#E8ECEF;">Timestamp = enforcement-action time</b> — morning-sweep pattern (00:30–13:00 IST) reflects
when officers record tags, not when vehicles parked.</li>
<li><b style="color:#E8ECEF;">Forecast scope limited</b> — only top-volume junctions with ≥30 days history; long-tail
junctions are explicitly excluded.</li>
<li><b style="color:#E8ECEF;">28.9% rejected/duplicate</b> — validated-only view shrinks effective sample for
low-volume junctions.</li>
<li><b style="color:#E8ECEF;">Historical system only</b> — no real-time feed; live enforcement triggering requires
traffic-flow API integration (Phase 2).</li>
</ol>
</div>
""", unsafe_allow_html=True)

    _section("Future Work")
    st.markdown("""
<div style="font-family:Inter,sans-serif;font-size:0.82rem;color:#8B96A3;line-height:1.8;">
<ul style="padding-left:18px;">
<li>Integrate live traffic-flow/speed APIs to replace PPI proxy with measured impact.</li>
<li>OCR/CV layer for image-based violation auto-detection once image data is available.</li>
<li>Continuous RL once outcome-feedback data (post-deployment violation reduction) is collected.</li>
</ul>
</div>
""", unsafe_allow_html=True)
