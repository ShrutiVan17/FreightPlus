# Data dictionary

This project uses a star-like logistics model. All data is synthetic.

| Table | Grain | Purpose |
|---|---|---|
| `shipments` | One row per inbound shipment | Service, delay, exception, damage, and freight-cost facts |
| `orders` | One row per purchase order | Supplier, priority, and order value; multiple orders may share a shipment |
| `routes` | One row per origin–facility lane | Distance and planned transit time |
| `carriers` | One row per fictional carrier | Contract rate, reliability, and capacity attributes |
| `facilities` | One row per fictional distribution facility | Region and daily pallet capacity |
| `inventory_snapshots` | Weekly facility-category snapshot | On-hand stock, target stock, and replenishment gap |

## Core KPI definitions

| KPI | Definition |
|---|---|
| On time | Actual delivery timestamp is at or before promised delivery timestamp |
| In full | Delivered units are greater than or equal to ordered units |
| OTIF | Shipment is both on time and in full |
| Exception rate | Shipments with an exception other than `No Exception` / analyzed shipments |
| Freight cost per unit | Total actual freight cost / total ordered units |
| Cost variance | Actual freight cost minus contracted freight cost |
| Late-arrival risk | Model-estimated probability that a dispatched shipment will miss its promise |

Service KPIs exclude rows missing an actual delivery timestamp. The quality report preserves the excluded count.

