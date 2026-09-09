# GhostRoute AI

**Autonomous Freight Disruption Recovery & Decision Intelligence**

GhostRoute is a hackathon-ready control tower that goes beyond delay prediction. It injects a live disruption, estimates SLA risk, evaluates recovery routes through a digital twin, models ETA uncertainty, ranks alternatives across business trade-offs, and produces an explainable human-approved recommendation.

## 60-second judge demo

1. Open `frontend/index.html`.
2. Click **INJECT DISRUPTION**.
3. Houston DC turns critical and Shipment GR-8472 is flagged at **84% SLA-breach risk**.
4. Watch the decision trace run risk scoring, digital-twin routing and Monte Carlo simulation.
5. Compare recovery alternatives.
6. Click **APPROVE RECOVERY** to record the human-in-the-loop decision.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md).

## Run frontend immediately

No dependencies:

```bash
cd ghostroute/frontend
python -m http.server 3000
```

Open http://localhost:3000

## Run API

```bash
cd ghostroute
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8080
```

API docs: http://localhost:8080/docs

## Run with Docker / Cloud Run

```bash
cd ghostroute
docker build -t ghostroute .
docker run -p 8080:8080 ghostroute
```

## Technical depth

- Event-driven disruption simulation
- Explainable shipment-risk scoring
- Transportation-network digital twin
- Multi-objective route recovery scoring
- 500-run Monte Carlo ETA simulation
- Cost and SLA exposure estimation
- Human-in-the-loop recovery approval
- Audit-ready decision IDs
- FastAPI serving layer
- Static dependency-free command-center UI

## Free-tier design

The core project requires **no paid AI API**. All decision numbers are produced by deterministic analytics. Gemini can later be added only as an optional narrative layer.

## Data statement

All shipment, facility, carrier, cost and operational values in this demo are synthetic and created solely for project demonstration. They are not Walmart, carrier, or customer production data.
