from pathlib import Path
import json
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
st.set_page_config(page_title="FreightPlus Control Tower", page_icon="🚚", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.6rem}.metric-card{background:#f6f3ff;border:1px solid #ded5f7;border-radius:14px;padding:14px}
h1,h2,h3{color:#33275f}div[data-testid='stMetric']{background:#faf9ff;border:1px solid #e7e1f5;padding:12px;border-radius:12px}
</style>""", unsafe_allow_html=True)

@st.cache_data
def load():
    s = pd.read_csv(ROOT/"data/processed/shipments_clean.csv", parse_dates=["ship_date"])
    return s, pd.read_csv(OUT/"carrier_scorecard.csv"), pd.read_csv(OUT/"lane_priority.csv"), pd.read_csv(OUT/"monthly_kpis.csv"), pd.read_csv(OUT/"shipment_risk_scores.csv"), json.load(open(OUT/"kpi_summary.json"))

s, carriers, lanes, monthly, risks, kpi = load()
st.title("FreightPlus — Inbound Logistics Control Tower")
st.caption("Synthetic retail transportation case study | Service • Cost • Exceptions • Predictive risk")

with st.sidebar:
    st.header("Filters")
    regions = st.multiselect("Region", sorted(s.region.dropna().unique()), default=sorted(s.region.dropna().unique()))
    modes = st.multiselect("Mode", sorted(s['mode'].unique()), default=sorted(s['mode'].unique()))
    dates = st.date_input("Ship date", [s.ship_date.min().date(), s.ship_date.max().date()])
f = s[s.region.isin(regions) & s['mode'].isin(modes)]
if len(dates)==2: f=f[(f.ship_date.dt.date>=dates[0])&(f.ship_date.dt.date<=dates[1])]
complete=f[f.record_complete_flag]

c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Shipments", f"{len(complete):,}")
c2.metric("OTIF", f"{complete.otif_flag.mean():.1%}")
c3.metric("Exception rate", f"{(complete.exception_code!='No Exception').mean():.1%}")
c4.metric("Freight cost", f"${complete.actual_freight_cost_usd.sum()/1e6:.1f}M")
c5.metric("Cost variance", f"${complete.cost_variance_usd.sum()/1e6:.2f}M")

tab1,tab2,tab3,tab4=st.tabs(["Executive view","Carriers & lanes","Exceptions","Risk queue"])
with tab1:
    m=complete.groupby(complete.ship_date.dt.to_period('M').astype(str),as_index=False).agg(otif_rate=('otif_flag','mean'),freight_cost=('actual_freight_cost_usd','sum'))
    a,b=st.columns(2)
    a.plotly_chart(px.line(m,x='ship_date',y='otif_rate',markers=True,title='Monthly OTIF',labels={'ship_date':'Month','otif_rate':'OTIF'}).update_yaxes(tickformat='.0%'),use_container_width=True)
    b.plotly_chart(px.bar(m,x='ship_date',y='freight_cost',title='Monthly freight spend',labels={'ship_date':'Month','freight_cost':'USD'}),use_container_width=True)
    fac=complete.groupby('facility_name',as_index=False).agg(shipments=('shipment_id','count'),otif_rate=('otif_flag','mean'),cost_variance=('cost_variance_usd','sum'))
    st.plotly_chart(px.scatter(fac,x='otif_rate',y='cost_variance',size='shipments',color='shipments',hover_name='facility_name',title='Facility service vs. cost exposure').update_xaxes(tickformat='.0%'),use_container_width=True)
with tab2:
    carrier=complete.groupby('carrier_name',as_index=False).agg(shipments=('shipment_id','count'),otif_rate=('otif_flag','mean'),cost_variance=('cost_variance_usd','sum'),avg_delay=('delay_hours','mean'))
    st.plotly_chart(px.scatter(carrier,x='otif_rate',y='cost_variance',size='shipments',color='avg_delay',hover_name='carrier_name',title='Carrier performance matrix').update_xaxes(tickformat='.0%'),use_container_width=True)
    st.subheader("Priority lanes")
    st.dataframe(lanes.head(15),use_container_width=True,hide_index=True)
with tab3:
    ex=complete[complete.exception_code!='No Exception'].groupby('exception_code',as_index=False).agg(shipments=('shipment_id','count'),avg_delay_hours=('delay_hours','mean'),cost_variance=('cost_variance_usd','sum'))
    a,b=st.columns(2)
    a.plotly_chart(px.bar(ex.sort_values('shipments'),x='shipments',y='exception_code',orientation='h',title='Exception volume'),use_container_width=True)
    b.plotly_chart(px.bar(ex.sort_values('cost_variance'),x='cost_variance',y='exception_code',orientation='h',title='Cost exposure by cause'),use_container_width=True)
with tab4:
    rb=risks.groupby('risk_band',observed=True).size().reset_index(name='shipments')
    st.plotly_chart(px.bar(rb,x='risk_band',y='shipments',color='risk_band',title='Late-arrival risk distribution',category_orders={'risk_band':['Low','Watch','High','Critical']}),use_container_width=True)
    st.dataframe(risks.sort_values('late_arrival_risk',ascending=False).head(30),use_container_width=True,hide_index=True)

st.caption("All companies, facilities, shipments, and operational results in this portfolio project are synthetic.")
