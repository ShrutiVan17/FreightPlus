-- PostgreSQL-compatible analytical schema
CREATE TABLE facilities (
  facility_id VARCHAR(8) PRIMARY KEY, facility_name VARCHAR(100), state CHAR(2),
  region VARCHAR(30), daily_capacity_pallets INTEGER
);
CREATE TABLE carriers (
  carrier_id VARCHAR(8) PRIMARY KEY, carrier_name VARCHAR(100),
  contract_rate_per_mile NUMERIC(8,2), base_reliability NUMERIC(5,3), capacity_index NUMERIC(5,2)
);
CREATE TABLE routes (
  route_id VARCHAR(8) PRIMARY KEY, origin VARCHAR(80),
  destination_facility_id VARCHAR(8) REFERENCES facilities(facility_id),
  distance_miles INTEGER, planned_transit_hours NUMERIC(8,1)
);
CREATE TABLE shipments (
  shipment_id VARCHAR(12) PRIMARY KEY, ship_date DATE, route_id VARCHAR(8) REFERENCES routes(route_id),
  carrier_id VARCHAR(8) REFERENCES carriers(carrier_id), facility_id VARCHAR(8), mode VARCHAR(20),
  product_category VARCHAR(40), pallets INTEGER, weight_lbs NUMERIC(12,1), ordered_units INTEGER,
  delivered_units INTEGER, promised_delivery_ts TIMESTAMP, actual_delivery_ts TIMESTAMP,
  on_time_flag BOOLEAN, in_full_flag BOOLEAN, otif_flag BOOLEAN, delay_hours NUMERIC(10,2),
  weather_risk_score NUMERIC(5,3), congestion_index NUMERIC(5,3), capacity_pressure NUMERIC(5,3),
  exception_code VARCHAR(50), contracted_cost_usd NUMERIC(12,2), actual_freight_cost_usd NUMERIC(12,2),
  cost_variance_usd NUMERIC(12,2), damage_flag BOOLEAN
);
CREATE INDEX idx_shipments_date ON shipments(ship_date);
CREATE INDEX idx_shipments_carrier ON shipments(carrier_id);
CREATE INDEX idx_shipments_route ON shipments(route_id);
CREATE INDEX idx_shipments_facility ON shipments(facility_id);
