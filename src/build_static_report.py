"""Create a portable interactive HTML executive report."""
from pathlib import Path
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
kpi = json.load(open(OUT / "kpi_summary.json"))
monthly = pd.read_csv(OUT / "monthly_kpis.csv")
carrier = pd.read_csv(OUT / "carrier_scorecard.csv").sort_values("otif_rate")
exceptions = pd.read_csv(OUT / "exception_summary.csv").sort_values("shipments")
lanes = pd.read_csv(OUT / "lane_priority.csv").head(10).sort_values("priority_score")

fig = make_subplots(rows=2, cols=2,
    subplot_titles=("Monthly OTIF", "Carrier OTIF", "Exception volume", "Priority lanes"),
    horizontal_spacing=.12, vertical_spacing=.20)
fig.add_trace(go.Scatter(x=monthly.year_month, y=monthly.otif_rate, mode="lines+markers", line=dict(color="#6d4bc3", width=3), name="OTIF"), 1, 1)
fig.add_trace(go.Bar(x=carrier.otif_rate, y=carrier.carrier_name, orientation="h", marker_color="#8a75c9", name="Carrier OTIF"), 1, 2)
fig.add_trace(go.Bar(x=exceptions.shipments, y=exceptions.exception_code, orientation="h", marker_color="#d58a78", name="Exceptions"), 2, 1)
fig.add_trace(go.Bar(x=lanes.priority_score, y=lanes.route_id + " | " + lanes.origin + " → " + lanes.facility_name, orientation="h", marker_color="#5f9c91", name="Lane priority"), 2, 2)
fig.update_xaxes(tickformat=".0%", row=1, col=2)
fig.update_yaxes(tickformat=".0%", range=[.72,.90], row=1, col=1)
fig.update_layout(height=950, template="plotly_white", showlegend=False,
    title=dict(text=f"FreightPlus Executive Control Tower<br><sup>{kpi['shipments_analyzed']:,} shipments | OTIF {kpi['otif_rate']:.1%} | Freight cost ${kpi['total_freight_cost_usd']/1e6:.1f}M | Cost variance ${kpi['cost_variance_usd']/1e6:.2f}M</sup>", x=.04),
    margin=dict(l=110,r=40,t=110,b=60), font=dict(family="Arial", color="#33275f"))
fig.write_html(ROOT / "executive_summary.html", include_plotlyjs=True, full_html=True)
print("Created executive_summary.html")
