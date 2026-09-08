"""Clean data, calculate logistics KPIs, and train an explainable delay-risk model."""

from pathlib import Path
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import roc_auc_score, precision_recall_fscore_support
from sklearn.metrics import f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT = Path(__file__).resolve().parents[1]
RAW, PROCESSED, OUTPUTS = ROOT / "data" / "raw", ROOT / "data" / "processed", ROOT / "outputs"


def main():
    PROCESSED.mkdir(parents=True, exist_ok=True)
    OUTPUTS.mkdir(parents=True, exist_ok=True)
    s = pd.read_csv(RAW / "shipments.csv", parse_dates=["ship_date", "promised_delivery_ts", "actual_delivery_ts"])
    routes = pd.read_csv(RAW / "routes.csv")
    carriers = pd.read_csv(RAW / "carriers.csv")
    facilities = pd.read_csv(RAW / "facilities.csv")

    quality_before = {
        "rows": int(len(s)), "duplicate_shipment_ids": int(s.shipment_id.duplicated().sum()),
        "missing_actual_delivery_ts": int(s.actual_delivery_ts.isna().sum()),
        "invalid_facility_ids": int((~s.facility_id.isin(facilities.facility_id)).sum()),
        "nonstandard_exception_codes": int((s.exception_code != s.exception_code.str.strip().str.title()).sum())
    }
    s = s.drop_duplicates("shipment_id", keep="first").copy()
    s["exception_code"] = s.exception_code.str.strip().str.title().replace({"No Exception": "No Exception"})
    route_facility = routes.set_index("route_id").destination_facility_id
    invalid = ~s.facility_id.isin(facilities.facility_id)
    s.loc[invalid, "facility_id"] = s.loc[invalid, "route_id"].map(route_facility)
    s["record_complete_flag"] = s.actual_delivery_ts.notna()
    s["year_month"] = s.ship_date.dt.to_period("M").astype(str)
    s["ship_month"] = s.ship_date.dt.month
    s["freight_cost_per_ordered_unit"] = s.actual_freight_cost_usd / s.ordered_units.clip(lower=1)
    s["cost_overrun_flag"] = s.cost_variance_usd > 0

    s = s.merge(routes[["route_id", "origin", "distance_miles", "planned_transit_hours"]], on="route_id", how="left")
    s = s.merge(carriers[["carrier_id", "carrier_name", "contract_rate_per_mile", "capacity_index"]], on="carrier_id", how="left")
    s = s.merge(facilities[["facility_id", "facility_name", "region"]], on="facility_id", how="left")

    complete = s[s.record_complete_flag].copy()
    kpis = {
        "shipments_analyzed": int(len(complete)),
        "otif_rate": round(float(complete.otif_flag.mean()), 4),
        "on_time_rate": round(float(complete.on_time_flag.mean()), 4),
        "in_full_rate": round(float(complete.in_full_flag.mean()), 4),
        "exception_rate": round(float((complete.exception_code != "No Exception").mean()), 4),
        "avg_delay_hours_late_shipments": round(float(complete.loc[complete.delay_hours > 0, "delay_hours"].mean()), 2),
        "total_freight_cost_usd": round(float(complete.actual_freight_cost_usd.sum()), 2),
        "cost_variance_usd": round(float(complete.cost_variance_usd.sum()), 2),
        "cost_per_ordered_unit_usd": round(float(complete.actual_freight_cost_usd.sum()/complete.ordered_units.sum()), 4),
        "data_quality_issues_found": int(sum(v for k,v in quality_before.items() if k != "rows")),
    }

    carrier_scorecard = complete.groupby(["carrier_id", "carrier_name"], as_index=False).agg(
        shipments=("shipment_id", "count"), otif_rate=("otif_flag", "mean"),
        avg_delay_hours=("delay_hours", "mean"), freight_cost=("actual_freight_cost_usd", "sum"),
        cost_variance=("cost_variance_usd", "sum"), damage_rate=("damage_flag", "mean"))
    carrier_scorecard["cost_per_shipment"] = carrier_scorecard.freight_cost/carrier_scorecard.shipments
    carrier_scorecard["performance_score"] = 100*(.65*carrier_scorecard.otif_rate + .20*(1-carrier_scorecard.damage_rate) + .15*(1-carrier_scorecard.avg_delay_hours/complete.delay_hours.quantile(.95)).clip(0,1))
    carrier_scorecard = carrier_scorecard.sort_values("performance_score", ascending=False)

    lane_scorecard = complete.groupby(["route_id", "origin", "facility_name", "distance_miles"], as_index=False).agg(
        shipments=("shipment_id", "count"), otif_rate=("otif_flag", "mean"),
        exception_rate=("exception_code", lambda x: (x != "No Exception").mean()),
        avg_delay_hours=("delay_hours", "mean"), cost_variance=("cost_variance_usd", "sum"))
    lane_scorecard["priority_score"] = 100*(.55*(1-lane_scorecard.otif_rate) + .25*lane_scorecard.exception_rate + .20*(lane_scorecard.cost_variance.clip(lower=0)/lane_scorecard.cost_variance.clip(lower=0).max()))
    lane_scorecard = lane_scorecard.sort_values("priority_score", ascending=False)

    monthly = complete.groupby("year_month", as_index=False).agg(
        shipments=("shipment_id", "count"), otif_rate=("otif_flag", "mean"),
        freight_cost=("actual_freight_cost_usd", "sum"), cost_variance=("cost_variance_usd", "sum"),
        exception_rate=("exception_code", lambda x: (x != "No Exception").mean()))

    # Predict late arrivals using only fields available at tender/dispatch time.
    features = ["carrier_id", "route_id", "facility_id", "mode", "product_category", "pallets", "weight_lbs", "distance_miles", "planned_transit_hours", "contracted_cost_usd", "capacity_index", "ship_month", "weather_risk_score", "congestion_index", "capacity_pressure"]
    model_df = complete.sort_values("ship_date")
    train_end, valid_end = int(len(model_df)*.70), int(len(model_df)*.85)
    train, valid, test = model_df.iloc[:train_end], model_df.iloc[train_end:valid_end], model_df.iloc[valid_end:]
    cat = ["carrier_id", "route_id", "facility_id", "mode", "product_category"]
    num = [c for c in features if c not in cat]
    prep = ColumnTransformer([
        ("cat", Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat),
        ("num", Pipeline([("impute", SimpleImputer(strategy="median"))]), num)
    ])
    model = Pipeline([("prep", prep), ("model", HistGradientBoostingClassifier(max_iter=180, learning_rate=.08, max_leaf_nodes=24, random_state=42))])
    model.fit(train[features], ~train.on_time_flag)
    valid_risk = model.predict_proba(valid[features])[:, 1]
    valid_y = (~valid.on_time_flag).astype(int)
    thresholds = np.arange(.08, .51, .01)
    threshold = float(max(thresholds, key=lambda t: f1_score(valid_y, valid_risk >= t, zero_division=0)))
    risk = model.predict_proba(test[features])[:, 1]
    pred = risk >= threshold
    y = (~test.on_time_flag).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    top_n = max(1, int(len(test)*.20))
    top_idx = np.argsort(risk)[-top_n:]
    risk_lift = y.iloc[top_idx].mean()/y.mean()
    alert_capture = y.iloc[top_idx].sum()/y.sum()
    model_metrics = {"roc_auc": round(float(roc_auc_score(y, risk)), 4), "decision_threshold": round(threshold,2), "precision": round(float(precision),4), "recall": round(float(recall),4), "f1": round(float(f1),4), "top_20pct_risk_lift": round(float(risk_lift),2), "top_20pct_late_shipments_captured": round(float(alert_capture),4), "test_rows": int(len(test))}
    scored = test[["shipment_id", "ship_date", "carrier_name", "origin", "facility_name", "mode", "otif_flag", "delay_hours", "cost_variance_usd"]].copy()
    scored["late_arrival_risk"] = np.round(risk, 4)
    scored["risk_band"] = pd.cut(scored.late_arrival_risk, [-.01,threshold*.60,threshold,threshold*1.60,1], labels=["Low","Watch","High","Critical"])

    exception_summary = complete[complete.exception_code != "No Exception"].groupby("exception_code", as_index=False).agg(
        shipments=("shipment_id", "count"), avg_delay_hours=("delay_hours", "mean"), cost_variance=("cost_variance_usd", "sum"))
    exception_summary = exception_summary.sort_values("shipments", ascending=False)

    s.to_csv(PROCESSED / "shipments_clean.csv", index=False)
    carrier_scorecard.to_csv(OUTPUTS / "carrier_scorecard.csv", index=False)
    lane_scorecard.to_csv(OUTPUTS / "lane_priority.csv", index=False)
    monthly.to_csv(OUTPUTS / "monthly_kpis.csv", index=False)
    scored.to_csv(OUTPUTS / "shipment_risk_scores.csv", index=False)
    exception_summary.to_csv(OUTPUTS / "exception_summary.csv", index=False)
    with open(OUTPUTS / "kpi_summary.json", "w") as f: json.dump(kpis, f, indent=2)
    with open(OUTPUTS / "data_quality_report.json", "w") as f: json.dump(quality_before, f, indent=2)
    with open(OUTPUTS / "model_metrics.json", "w") as f: json.dump(model_metrics, f, indent=2)
    print(json.dumps({"kpis": kpis, "model": model_metrics}, indent=2))


if __name__ == "__main__":
    main()
