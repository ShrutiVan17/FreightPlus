from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import random
import math

app = FastAPI(title="GhostRoute AI Decision API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Disruption(BaseModel):
    shipment_id: str = "GR-8472"
    scenario: str = "Houston warehouse congestion"
    severity: str = "critical"

ROUTES = [
    {"name":"Current Route","hours":18.4,"extra_cost":0,"base_risk":0.84,"hub":"Houston"},
    {"name":"Dallas Hub B","hours":13.1,"extra_cost":42,"base_risk":0.21,"hub":"Dallas"},
    {"name":"San Antonio Relay","hours":11.9,"extra_cost":108,"base_risk":0.14,"hub":"San Antonio"},
    {"name":"Hold / Recover","hours":24.7,"extra_cost":-15,"base_risk":0.96,"hub":"Houston"},
]

def monte_carlo(hours: float, risk: float, n: int = 500):
    samples = []
    for _ in range(n):
        shock = random.gauss(0, 1.15 + risk * 2.2)
        samples.append(max(hours + shock, hours * 0.65))
    samples.sort()
    p10 = samples[int(n*0.10)]
    p90 = samples[int(n*0.90)]
    mean = sum(samples)/len(samples)
    return round(mean,1), round(p10,1), round(p90,1)

def score(route):
    # Higher is better. Transparent deterministic multi-objective score.
    sla_component = (1-route["base_risk"]) * 45
    time_component = max(0, 30 - route["hours"])
    cost_component = max(0, 25 - max(route["extra_cost"],0)/6)
    return round(min(100, sla_component + time_component + cost_component), 1)

@app.get("/health")
def health():
    return {"status":"ok","service":"ghostroute"}

@app.get("/api/network")
def network():
    return {
      "nodes":[
        {"id":"HOU","name":"Houston DC","x":22,"y":68},
        {"id":"DAL","name":"Dallas Hub","x":48,"y":30},
        {"id":"SAT","name":"San Antonio Relay","x":35,"y":80},
        {"id":"MEM","name":"Memphis Gateway","x":77,"y":25},
        {"id":"ATL","name":"Atlanta Customer","x":90,"y":58},
      ],
      "edges":[
        ["HOU","ATL"],["HOU","DAL"],["DAL","MEM"],["MEM","ATL"],
        ["HOU","SAT"],["SAT","ATL"]
      ]
    }

@app.post("/api/disrupt")
def disrupt(payload: Disruption):
    evaluated = []
    for r in ROUTES:
        mean,p10,p90 = monte_carlo(r["hours"], r["base_risk"])
        exposure = round(2900*r["base_risk"] + max(r["extra_cost"],0), 0)
        evaluated.append({
            **r,
            "score": score(r),
            "eta_mean":mean,
            "eta_p10":p10,
            "eta_p90":p90,
            "financial_exposure":exposure
        })

    alternatives = sorted(evaluated, key=lambda x:x["score"], reverse=True)
    best = alternatives[0]
    baseline = next(x for x in evaluated if x["name"]=="Current Route")
    avoided = round(baseline["financial_exposure"] - best["financial_exposure"], 0)
    delay_saved = round(baseline["eta_mean"] - best["eta_mean"],1)

    return {
      "incident":{
        "shipment_id":payload.shipment_id,
        "scenario":payload.scenario,
        "severity":payload.severity,
        "risk_probability":0.84,
        "expected_delay_hours":6.7,
        "primary_driver":"Warehouse dwell-time spike",
        "drivers":[
          {"name":"Warehouse dwell time","impact":31},
          {"name":"Historical lane delay","impact":22},
          {"name":"Carrier reliability","impact":14},
          {"name":"Distance remaining","impact":11},
          {"name":"Regional disruption","impact":8},
        ]
      },
      "recommendation":{
        "action":f"Reroute through {best['name']}",
        "route":best["name"],
        "delay_saved_hours":delay_saved,
        "incremental_cost":best["extra_cost"],
        "exposure_avoided":avoided,
        "reason":(
          f"{best['name']} has the strongest combined SLA, cost, and time score. "
          f"It cuts modeled delay by {delay_saved} hours while adding "
          f"${best['extra_cost']} in transport cost."
        )
      },
      "alternatives":alternatives,
      "audit_id":"AUD-GR-2026-0909-001"
    }
