<div align="center">

# FreightPlus

### Inbound Logistics Control Tower

[![OPEN LIVE DASHBOARD](https://img.shields.io/badge/OPEN_LIVE_DASHBOARD-7357E8?style=for-the-badge&logo=github&logoColor=white)](https://shrutivan17.github.io/FreightPlus/)

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Dashboard](https://img.shields.io/badge/Dashboard-Interactive-17B99A)
![FreightPlus CI](https://github.com/ShrutiVan17/FreightPlus/actions/workflows/ci.yml/badge.svg)

</div>

[![FreightPlus dashboard](assets/freightplus_dashboard_preview.svg)](https://shrutivan17.github.io/FreightPlus/)

| **54,840** shipments | **81.2%** OTIF | **$163.3M** freight spend | **1.68×** risk lift |
|:---:|:---:|:---:|:---:|

## Explore

| Live view | Decision |
|---|---|
| Service pulse | Track OTIF and on-time delivery |
| Carrier scorecards | Compare service, delay, damage and cost |
| Exception map | Find capacity, congestion and weather exposure |
| Risk queue | Prioritize shipments before the promise is missed |

## Flow

```mermaid
flowchart LR
    A["6 source tables"] --> B["Quality pipeline"]
    B --> C["KPI layer"]
    B --> D["Delay model"]
    C --> E["Control tower"]
    D --> E
```

## Stack

`Python` · `Pandas` · `scikit-learn` · `PostgreSQL` · `Streamlit` · `JavaScript` · `Docker` · `GitHub Actions`

## Run

```bash
pip install -r requirements.txt
python src/generate_data.py
python src/analyze.py
streamlit run app.py
```

> All carriers, facilities, shipments and operational results are synthetic. No retailer data is used.
