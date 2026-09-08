"""Render a static recruiter-facing dashboard preview from validated outputs."""
from pathlib import Path
import json
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
ASSETS = ROOT / "assets"
ASSETS.mkdir(exist_ok=True)

k = json.load(open(OUT / "kpi_summary.json"))
monthly = pd.read_csv(OUT / "monthly_kpis.csv")
carrier = pd.read_csv(OUT / "carrier_scorecard.csv").sort_values("otif_rate").tail(8)
exceptions = pd.read_csv(OUT / "exception_summary.csv").sort_values("shipments").tail(6)

plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})
fig = plt.figure(figsize=(16, 9), facecolor="#f7f5fb")
gs = fig.add_gridspec(3, 4, height_ratios=[.72, 2.3, 2.3], hspace=.48, wspace=.52)
fig.suptitle("FreightPlus  |  Inbound Logistics Control Tower", x=.05, y=.98, ha="left", fontsize=23, fontweight="bold", color="#33275f")
fig.text(.05, .94, "Service  •  Cost  •  Exceptions  •  Predictive Risk", fontsize=11, color="#746a8f")

cards = [("SHIPMENTS", f"{k['shipments_analyzed']:,}"), ("OTIF", f"{k['otif_rate']:.1%}"),
         ("FREIGHT SPEND", f"${k['total_freight_cost_usd']/1e6:.1f}M"), ("COST VARIANCE", f"${k['cost_variance_usd']/1e6:.2f}M")]
for i, (label, value) in enumerate(cards):
    ax = fig.add_subplot(gs[0, i]); ax.set_facecolor("white")
    for s in ax.spines.values(): s.set_color("#ddd6ef")
    ax.set_xticks([]); ax.set_yticks([])
    ax.text(.06,.70,label,transform=ax.transAxes,fontsize=9,color="#746a8f",fontweight="bold")
    ax.text(.06,.19,value,transform=ax.transAxes,fontsize=20,color="#33275f",fontweight="bold")

ax1=fig.add_subplot(gs[1, :2]); ax1.set_facecolor("white")
ax1.plot(monthly.year_month, monthly.otif_rate*100, color="#6d4bc3", lw=2.8, marker="o", ms=4)
ax1.fill_between(range(len(monthly)), monthly.otif_rate*100, 75, color="#dcd3f4", alpha=.55)
ax1.set_title("Monthly OTIF trend", loc="left", color="#33275f"); ax1.set_ylabel("OTIF %"); ax1.tick_params(axis="x", rotation=45, labelsize=7)
ax1.grid(axis="y", alpha=.18); ax1.spines[['top','right']].set_visible(False)

ax2=fig.add_subplot(gs[1, 2:]); ax2.set_facecolor("white")
ax2.barh(carrier.carrier_name, carrier.otif_rate*100, color="#8170bc")
ax2.set_title("Top carrier OTIF", loc="left", color="#33275f"); ax2.set_xlabel("OTIF %"); ax2.set_xlim(78,87)
ax2.grid(axis="x", alpha=.18); ax2.spines[['top','right']].set_visible(False)

ax3=fig.add_subplot(gs[2, :2]); ax3.set_facecolor("white")
ax3.barh(exceptions.exception_code, exceptions.shipments, color="#d58a78")
ax3.set_title("Exception volume by root cause", loc="left", color="#33275f"); ax3.set_xlabel("Shipments")
ax3.grid(axis="x", alpha=.18); ax3.spines[['top','right']].set_visible(False)

ax4=fig.add_subplot(gs[2, 2:]); ax4.set_facecolor("white"); ax4.axis("off")
ax4.set_title("Planner action brief", loc="left", color="#33275f", pad=10)
actions=[("01","Protect high-risk loads","Top-risk 20% captures 33.6% of late shipments"),
         ("02","Correct capacity failures","Largest exception category: 2,066 shipments"),
         ("03","Fix priority lane","Detroit → Houston OTIF: 75.9%"),
         ("04","Reduce cost leakage",f"${k['cost_variance_usd']/1e6:.2f}M above contract")]
for j,(num,title,detail) in enumerate(actions):
    y=.83-j*.22
    ax4.text(.02,y,num,fontsize=12,fontweight="bold",color="white",bbox=dict(boxstyle="round,pad=.38",fc="#6d4bc3",ec="none"))
    ax4.text(.13,y+.025,title,fontsize=12,fontweight="bold",color="#33275f")
    ax4.text(.13,y-.055,detail,fontsize=9.5,color="#746a8f")

fig.text(.05,.02,"Synthetic portfolio case study • Reproducible fixed-seed pipeline • No retailer data used",fontsize=9,color="#746a8f")
fig.savefig(ASSETS/"freightplus_dashboard_preview.svg", bbox_inches="tight", facecolor=fig.get_facecolor())
print("Created assets/freightplus_dashboard_preview.svg")
