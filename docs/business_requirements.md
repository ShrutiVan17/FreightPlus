# Business requirements document

## 1. Business problem

Inbound transportation planners lack one view connecting carrier service, lane exceptions, facility exposure, freight-cost variance, and shipment-level delay risk. Manual follow-up begins after a load is already late, limiting recovery options.

## 2. Objective

Build a planner control tower that identifies where service or cost is deteriorating, explains the operational cause, and creates a prioritized pre-arrival intervention queue.

## 3. Stakeholders and decisions

| Stakeholder | Decision supported |
|---|---|
| Transportation planner | Which active shipments should be contacted first? |
| Carrier manager | Which carriers need a corrective action plan or volume rebalance? |
| Facility operations lead | Which receiving locations are accumulating delay and cost exposure? |
| Finance partner | Where is actual freight spend exceeding contracted cost? |
| Data steward | Which records are incomplete, duplicated, or unmapped? |

## 4. Functional requirements

1. Filter performance by date, region, transportation mode, carrier, facility, and lane.
2. Show shipment volume, OTIF, on-time, in-full, exception rate, freight spend, and cost variance.
3. Rank carriers using service, delay, damage, and cost measures.
4. Rank lanes using OTIF failure, exception incidence, and positive cost variance.
5. Display root-cause volume and associated cost exposure.
6. Score dispatched shipments using fields available before arrival.
7. Preserve excluded incomplete records in a visible data-quality report.

## 5. Business rules

- `on_time = actual_delivery_ts <= promised_delivery_ts`
- `in_full = delivered_units >= ordered_units`
- `OTIF = on_time AND in_full`
- Service KPIs exclude shipments with a missing actual-delivery timestamp.
- Cost variance equals actual freight cost minus contracted freight cost.
- A lane enters the priority table only after sufficient shipment volume is available.
- Model threshold selection uses a validation time period; the final metrics use a later, untouched test period.

## 6. Acceptance criteria

| ID | Criterion | Verification |
|---|---|---|
| AC-01 | Duplicate shipment IDs are detected and removed from analytical grain | `data_quality_report.json` and uniqueness test |
| AC-02 | Invalid facility IDs are repaired from the route master | Referential-integrity test |
| AC-03 | Dashboard totals reconcile to processed data | Automated KPI comparison |
| AC-04 | No future delivery outcome is used as a model feature | Feature-list review |
| AC-05 | Model evaluation respects time order | Chronological train/validation/test split |
| AC-06 | Synthetic status is clear | README, dashboard footer, and data dictionary |

## 7. Out of scope

Live carrier APIs, real company data, dispatch execution, freight tendering, and production model monitoring are not included in this portfolio release.

