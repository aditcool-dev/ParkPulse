---
title: ParkPulse
emoji: 🚦
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: "1.37.1"
app_file: app.py
pinned: false
---

# ParkPulse — Parking Enforcement Intelligence

Flipkart GRID PS1 prototype. Detects illegal-parking hotspots in Bangalore,
scores them by Parking Pressure Index (PPI), forecasts next-day violations,
and allocates patrol units via MILP optimization.

**Pipeline**: DBSCAN clustering → PPI scoring → LightGBM forecast → PuLP MILP allocation  
**Data**: 298,450 violation records, Nov 2023 – Apr 2024, Bangalore  
**Dashboard**: 4 screens — Overview map, Hotspot Detail, Patrol Allocation, Methodology
