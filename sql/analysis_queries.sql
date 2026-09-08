-- 1. Executive KPI view (exclude incomplete delivery records from service metrics)
SELECT
  COUNT(*) AS shipments,
  ROUND(100.0 * AVG(CASE WHEN otif_flag THEN 1 ELSE 0 END), 2) AS otif_pct,
  ROUND(100.0 * AVG(CASE WHEN on_time_flag THEN 1 ELSE 0 END), 2) AS on_time_pct,
  ROUND(SUM(actual_freight_cost_usd), 2) AS freight_spend,
  ROUND(SUM(cost_variance_usd), 2) AS cost_variance
FROM shipments WHERE actual_delivery_ts IS NOT NULL;

-- 2. Carrier scorecard
SELECT c.carrier_name, COUNT(*) shipments,
  ROUND(100.0*AVG(CASE WHEN s.otif_flag THEN 1 ELSE 0 END),2) otif_pct,
  ROUND(AVG(s.delay_hours),2) avg_delay_hours,
  ROUND(SUM(s.cost_variance_usd),2) cost_variance,
  ROUND(100.0*AVG(CASE WHEN s.damage_flag THEN 1 ELSE 0 END),2) damage_pct
FROM shipments s JOIN carriers c USING (carrier_id)
WHERE s.actual_delivery_ts IS NOT NULL
GROUP BY c.carrier_name ORDER BY otif_pct DESC, cost_variance;

-- 3. Lanes requiring planner intervention
SELECT r.route_id, r.origin, f.facility_name, COUNT(*) shipments,
  ROUND(100.0*AVG(CASE WHEN s.otif_flag THEN 1 ELSE 0 END),2) otif_pct,
  ROUND(100.0*AVG(CASE WHEN s.exception_code <> 'No Exception' THEN 1 ELSE 0 END),2) exception_pct,
  ROUND(SUM(s.cost_variance_usd),2) cost_exposure
FROM shipments s JOIN routes r USING(route_id)
JOIN facilities f ON f.facility_id=r.destination_facility_id
WHERE s.actual_delivery_ts IS NOT NULL
GROUP BY r.route_id,r.origin,f.facility_name
HAVING COUNT(*) >= 100
ORDER BY otif_pct, cost_exposure DESC LIMIT 20;

-- 4. Root-cause Pareto with cumulative exception share
WITH x AS (
 SELECT exception_code, COUNT(*) shipments, SUM(cost_variance_usd) cost_exposure
 FROM shipments WHERE exception_code <> 'No Exception' GROUP BY exception_code
)
SELECT *, ROUND(100.0*SUM(shipments) OVER(ORDER BY shipments DESC)/SUM(shipments) OVER(),2) cumulative_pct
FROM x ORDER BY shipments DESC;

-- 5. Month-over-month service trend
SELECT DATE_TRUNC('month',ship_date) month, COUNT(*) shipments,
 ROUND(100.0*AVG(CASE WHEN otif_flag THEN 1 ELSE 0 END),2) otif_pct,
 ROUND(SUM(actual_freight_cost_usd),2) freight_spend
FROM shipments WHERE actual_delivery_ts IS NOT NULL
GROUP BY 1 ORDER BY 1;

-- 6. Automated data-quality checks
SELECT 'duplicate_shipment_id' issue, COUNT(*) affected
FROM (SELECT shipment_id FROM shipments GROUP BY shipment_id HAVING COUNT(*)>1) d
UNION ALL SELECT 'missing_actual_delivery_ts',COUNT(*) FROM shipments WHERE actual_delivery_ts IS NULL
UNION ALL SELECT 'unmapped_facility',COUNT(*) FROM shipments s LEFT JOIN facilities f USING(facility_id) WHERE f.facility_id IS NULL;

