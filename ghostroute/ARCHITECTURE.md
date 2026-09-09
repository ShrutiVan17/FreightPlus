# GhostRoute AI — Architecture

GhostRoute AI is an event-driven freight disruption recovery platform designed to detect shipment risk, evaluate recovery options, and produce an explainable operational decision.

## System Architecture

```mermaid
flowchart LR
    subgraph Sources["Operational Signals"]
      S1["Shipment Events"]
      S2["Carrier Performance"]
      S3["Facility Capacity"]
      S4["Weather / Congestion Simulator"]
    end

    subgraph Ingestion["Event & Feature Layer"]
      I1["Event Normalizer"]
      I2["Feature Builder"]
      I3["Scenario Injector"]
    end

    subgraph Intelligence["Decision Intelligence"]
      M1["Risk Engine\nDelay Probability"]
      M2["Network Digital Twin\nGraph Optimization"]
      M3["Monte Carlo Engine\nETA Uncertainty"]
      M4["Cost / SLA Engine"]
      M5["Explainability Engine"]
    end

    subgraph Orchestration["Recovery Orchestrator"]
      A1["Risk Agent"]
      A2["Route Agent"]
      A3["Cost Agent"]
      A4["Operations Decision"]
    end

    subgraph API["Serving Layer"]
      API1["FastAPI Decision API"]
      API2["Audit Trail"]
    end

    subgraph UI["Control Tower"]
      U1["Network Map"]
      U2["Incident Queue"]
      U3["Recovery Comparison"]
      U4["Approve / Reject"]
      U5["Executive KPIs"]
    end

    S1 --> I1
    S2 --> I1
    S3 --> I1
    S4 --> I3
    I1 --> I2
    I3 --> I2
    I2 --> M1
    I2 --> M2
    I2 --> M3
    M1 --> M4
    M2 --> M4
    M3 --> M4
    M1 --> M5
    M4 --> A1
    M2 --> A2
    M4 --> A3
    A1 --> A4
    A2 --> A4
    A3 --> A4
    M5 --> A4
    A4 --> API1
    API1 --> U1
    API1 --> U2
    API1 --> U3
    U4 --> API2
    API2 --> U5
```

## Why this architecture is strong

### 1. Event-driven, not dashboard-only
A disruption is injected as an operational event. The platform recomputes shipment risk and recovery options immediately.

### 2. Digital twin
The transportation network is modeled as a graph. Recovery alternatives are evaluated as network paths rather than hard-coded text.

### 3. Uncertainty-aware decisions
Monte Carlo simulation produces an ETA distribution and SLA-breach probability instead of pretending one ETA is certain.

### 4. Multi-objective recovery
Every route is scored across delay, cost, SLA risk, and operational feasibility.

### 5. Explainable decision layer
The system reports the drivers behind a risk score and the trade-off behind the recommended recovery.

### 6. Human-in-the-loop
GhostRoute recommends actions; a user approves or rejects them. Decisions are auditable.

## Free-tier deployment profile

The submission does not require paid AI APIs. The deterministic decision engine runs locally or in one small Cloud Run service.

- Frontend: static HTML/CSS/JavaScript
- API: FastAPI
- Data: synthetic JSON/in-memory for demo
- Optional persistence: Firestore
- Optional analytics: BigQuery sandbox/free usage
- Optional LLM narrative: Gemini can be added later, but is not required

Recommended Cloud Run configuration:

```
min instances: 0
max instances: 1
CPU: 1
memory: 512 MiB
concurrency: 20
```

## Request path

```
Judge clicks "Inject Disruption"
        ↓
POST /api/disrupt
        ↓
Scenario event created
        ↓
Risk score recalculated
        ↓
Alternative paths generated
        ↓
Monte Carlo ETA simulation
        ↓
Cost + SLA trade-off ranking
        ↓
Explainable recommendation
        ↓
Dashboard updates
        ↓
Judge approves / rejects action
```

## Design principle

The AI layer is not allowed to invent operational numbers. Numeric decisions come from deterministic analytics and optimization. A language model, if enabled later, only translates those grounded results into natural-language explanations.
