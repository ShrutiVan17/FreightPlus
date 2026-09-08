"""Generate a reproducible synthetic retail inbound-logistics dataset."""

from pathlib import Path
import numpy as np
import pandas as pd

SEED = 20260908
N_SHIPMENTS = 55_000
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def main():
    rng = np.random.default_rng(SEED)
    RAW.mkdir(parents=True, exist_ok=True)

    facilities = pd.DataFrame([
        ("FC01", "Bentonville DC", "AR", "Central", 1180),
        ("FC02", "Dallas DC", "TX", "South", 1420),
        ("FC03", "Houston DC", "TX", "South", 1310),
        ("FC04", "Atlanta DC", "GA", "Southeast", 1250),
        ("FC05", "Chicago DC", "IL", "Midwest", 1390),
        ("FC06", "Phoenix DC", "AZ", "West", 1120),
        ("FC07", "Ontario DC", "CA", "West", 1490),
        ("FC08", "Denver DC", "CO", "Mountain", 970),
        ("FC09", "Columbus DC", "OH", "Midwest", 1230),
        ("FC10", "Allentown DC", "PA", "Northeast", 1280),
        ("FC11", "Savannah Import Center", "GA", "Southeast", 890),
        ("FC12", "Long Beach Import Center", "CA", "West", 940),
    ], columns=["facility_id", "facility_name", "state", "region", "daily_capacity_pallets"])

    carriers = pd.DataFrame({
        "carrier_id": [f"CR{i:02d}" for i in range(1, 16)],
        "carrier_name": [
            "Atlas Freight", "BlueRiver Logistics", "Cedar Linehaul", "DeltaWay Transport",
            "Evergreen Haul", "Frontier Cargo", "Great Plains Express", "HarborLink",
            "Interstate North", "Juniper Freight", "Keystone Transport", "Lone Star Haul",
            "MetroFleet", "NorthPeak Logistics", "Ozark Express"
        ],
        "contract_rate_per_mile": np.round(rng.uniform(1.78, 2.78, 15), 2),
        "base_reliability": np.round(rng.uniform(0.84, 0.97, 15), 3),
        "capacity_index": np.round(rng.uniform(0.78, 1.20, 15), 2),
    })

    origins = ["Los Angeles CA", "Savannah GA", "Laredo TX", "Memphis TN", "Kansas City MO",
               "Seattle WA", "Newark NJ", "Miami FL", "Louisville KY", "Detroit MI",
               "Charlotte NC", "Salt Lake City UT", "Omaha NE", "Nashville TN", "El Paso TX"]
    route_rows = []
    rid = 1
    for origin in origins:
        chosen = rng.choice(facilities.facility_id, size=8, replace=False)
        for dest in chosen:
            distance = int(rng.integers(180, 2200))
            route_rows.append((f"RT{rid:03d}", origin, dest, distance, round(distance / 50 + 8, 1)))
            rid += 1
    routes = pd.DataFrame(route_rows, columns=["route_id", "origin", "destination_facility_id", "distance_miles", "planned_transit_hours"])

    n = N_SHIPMENTS
    ship_date = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 547, n), unit="D")
    route_idx = rng.integers(0, len(routes), n)
    carrier_weights = np.array([8,7,7,8,6,7,7,6,7,6,7,8,6,7,10], dtype=float)
    carrier_idx = rng.choice(len(carriers), n, p=carrier_weights/carrier_weights.sum())
    route = routes.iloc[route_idx].reset_index(drop=True)
    carrier = carriers.iloc[carrier_idx].reset_index(drop=True)
    mode = rng.choice(["Truckload", "LTL", "Intermodal"], n, p=[0.62, 0.27, 0.11])
    product_category = rng.choice(["Grocery", "General Merchandise", "Electronics", "Home", "Apparel", "Health & Beauty"], n,
                                  p=[0.27, 0.20, 0.12, 0.15, 0.13, 0.13])
    pallets = np.maximum(1, rng.poisson(np.where(mode == "Truckload", 22, np.where(mode == "LTL", 7, 18))))
    weight = np.round(pallets * rng.uniform(550, 1250, n), 0)
    promised_hours = route.planned_transit_hours.to_numpy() * np.where(mode == "Intermodal", 1.35, np.where(mode == "LTL", 1.18, 1.0))
    promised_ts = ship_date + pd.to_timedelta(promised_hours, unit="h")

    miles = route.distance_miles.to_numpy()
    month = ship_date.month.to_numpy()
    peak = np.isin(month, [10, 11, 12]).astype(float)
    weather_risk_score = np.clip(.05 + .20*np.isin(month, [1,2,7,8]) + .55*rng.beta(1.4,5.2,n), 0, 1)
    congestion_index = np.clip(.08 + .12*peak + .15*(miles > 1400) + .55*rng.beta(1.7,4.8,n), 0, 1)
    capacity_pressure = np.clip(.15 + .22*peak + .35*(1/carrier.capacity_index.to_numpy()-0.8) + .40*rng.beta(1.5,4.5,n), 0, 1)
    weather = rng.binomial(1, weather_risk_score*.42)
    congestion = rng.binomial(1, congestion_index*.48)
    capacity = rng.binomial(1, capacity_pressure*.44)
    documentation = rng.binomial(1, 0.035 + 0.03 * np.isin(route.origin.to_numpy(), ["Laredo TX", "Savannah GA", "Los Angeles CA"]))
    mechanical = rng.binomial(1, 0.025, n)
    reliability = carrier.base_reliability.to_numpy()
    delay_probability = sigmoid(-5.0 + 1.65*weather + 1.20*congestion + 1.35*capacity + 1.2*documentation + 1.7*mechanical + 4.2*(0.91-reliability) + 3.0*weather_risk_score + 2.4*congestion_index + 2.5*capacity_pressure + 0.25*peak)
    delayed = rng.random(n) < delay_probability
    delay_hours = np.where(delayed, np.maximum(0.5, rng.gamma(2.2, 6.0, n) + 8*weather + 5*mechanical), -rng.uniform(0.5, 8, n))
    actual_ts = promised_ts + pd.to_timedelta(delay_hours, unit="h")

    exception = np.full(n, "No Exception", dtype=object)
    candidates = np.column_stack([weather, congestion, capacity, documentation, mechanical])
    labels = np.array(["Weather", "Port/Traffic Congestion", "Carrier Capacity", "Documentation", "Mechanical"])
    for i in np.where(delayed)[0]:
        active = np.flatnonzero(candidates[i])
        exception[i] = labels[rng.choice(active)] if len(active) else rng.choice(["Late Pickup", "Facility Dwell", "Unclassified"], p=[.45,.35,.20])

    base_cost = miles * carrier.contract_rate_per_mile.to_numpy() * np.where(mode == "LTL", 0.58, np.where(mode == "Intermodal", 0.82, 1.0))
    fuel = miles * rng.uniform(0.34, 0.52, n)
    accessorial = np.where(delayed, rng.gamma(1.6, 105, n), rng.gamma(0.5, 25, n))
    actual_cost = np.round(base_cost + fuel + accessorial + rng.normal(0, 55, n), 2)
    contracted_cost = np.round(base_cost + miles*0.40, 2)
    damage_flag = rng.random(n) < (0.008 + 0.012*delayed + 0.006*(mode == "LTL"))
    quantity = np.maximum(1, (pallets * rng.integers(35, 95, n))).astype(int)
    delivered_quantity = np.maximum(
        0,
        quantity - damage_flag*rng.integers(1, 20, n) - (rng.random(n)<0.018)*rng.integers(1, 35, n)
    ).astype(int)
    in_full = delivered_quantity >= quantity
    on_time = actual_ts <= promised_ts

    shipments = pd.DataFrame({
        "shipment_id": [f"SHP{i:06d}" for i in range(1, n+1)],
        "ship_date": ship_date, "route_id": route.route_id, "carrier_id": carrier.carrier_id,
        "facility_id": route.destination_facility_id, "mode": mode, "product_category": product_category,
        "pallets": pallets, "weight_lbs": weight, "ordered_units": quantity,
        "delivered_units": delivered_quantity, "promised_delivery_ts": promised_ts,
        "actual_delivery_ts": actual_ts, "on_time_flag": on_time, "in_full_flag": in_full,
        "otif_flag": on_time & in_full, "delay_hours": np.round(np.maximum(delay_hours, 0), 2),
        "weather_risk_score": np.round(weather_risk_score, 3),
        "congestion_index": np.round(congestion_index, 3),
        "capacity_pressure": np.round(capacity_pressure, 3),
        "exception_code": exception, "contracted_cost_usd": contracted_cost,
        "actual_freight_cost_usd": actual_cost, "cost_variance_usd": np.round(actual_cost-contracted_cost, 2),
        "damage_flag": damage_flag
    })

    # Inject a small, documented set of quality issues for the profiling pipeline to catch.
    issue_idx = rng.choice(n, 520, replace=False)
    shipments.loc[issue_idx[:160], "actual_delivery_ts"] = pd.NaT
    shipments.loc[issue_idx[160:300], "exception_code"] = "late pickup "
    shipments.loc[issue_idx[300:410], "facility_id"] = "UNKNOWN"
    duplicate_rows = shipments.loc[issue_idx[410:]].copy()
    shipments = pd.concat([shipments, duplicate_rows], ignore_index=True)

    # One-to-many purchase orders allow order-level cost and service analysis.
    order_counts = rng.choice([1, 2, 3], n, p=[.69, .25, .06])
    shipment_ids = np.repeat([f"SHP{i:06d}" for i in range(1, n+1)], order_counts)
    m = len(shipment_ids)
    orders = pd.DataFrame({
        "order_id": [f"PO{i:07d}" for i in range(1, m+1)],
        "shipment_id": shipment_ids,
        "supplier_id": [f"SUP{x:04d}" for x in rng.integers(1, 901, m)],
        "order_value_usd": np.round(rng.lognormal(9.0, 0.75, m), 2),
        "priority": rng.choice(["Standard", "Expedite", "Critical"], m, p=[.82,.14,.04])
    })

    # Facility/category inventory snapshots for stockout exposure analysis.
    snapshot_dates = pd.date_range("2025-01-01", "2026-06-30", freq="7D")
    inv_rows = []
    categories = ["Grocery", "General Merchandise", "Electronics", "Home", "Apparel", "Health & Beauty"]
    for d in snapshot_dates:
        for f in facilities.facility_id:
            for c in categories:
                target = int(rng.integers(1200, 8200))
                on_hand = max(0, int(target * rng.uniform(.45, 1.35)))
                inv_rows.append((d, f, c, on_hand, target, max(0, target-on_hand)))
    inventory = pd.DataFrame(inv_rows, columns=["snapshot_date", "facility_id", "product_category", "on_hand_units", "target_units", "replenishment_gap_units"])

    for name, df in {"facilities": facilities, "carriers": carriers, "routes": routes,
                     "shipments": shipments, "orders": orders, "inventory_snapshots": inventory}.items():
        df.to_csv(RAW / f"{name}.csv", index=False)

    print(f"Generated {len(shipments):,} shipment rows, {len(orders):,} orders, and {len(inventory):,} inventory snapshots.")


if __name__ == "__main__":
    main()
