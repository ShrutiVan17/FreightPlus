import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

def test_analytical_grain_is_unique():
    s = pd.read_csv(ROOT/"data/processed/shipments_clean.csv")
    assert s.shipment_id.is_unique

def test_dimensions_reconcile():
    s = pd.read_csv(ROOT/"data/processed/shipments_clean.csv")
    assert s.facility_name.notna().all()
    assert s.carrier_name.notna().all()

def test_kpis_are_valid():
    k = json.load(open(ROOT/"outputs/kpi_summary.json"))
    assert 0 <= k["otif_rate"] <= 1
    assert k["shipments_analyzed"] > 50_000
    assert k["data_quality_issues_found"] == 520
