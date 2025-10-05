from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np
import json
import os

# --- 1. Initialize FastAPI app and enable CORS ---
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST"],
    allow_headers=["*"],
)

# --- 2. Load Telemetry Data at Startup ---
# Get the directory of the current script to build the correct file path.
# This ensures it works correctly in the Vercel serverless environment.
api_dir = os.path.dirname(os.path.abspath(__file__))
telemetry_path = os.path.join(api_dir, '..', 'telemetry.json')

with open(telemetry_path, 'r') as f:
    telemetry_data = json.load(f)

# --- 3. Define Pydantic Models for Request Body ---
class MetricsRequest(BaseModel):
    regions: List[str]
    threshold_ms: int

# --- 4. Define the POST Endpoint for Metrics ---
@app.post("/metrics")
def get_metrics(request: MetricsRequest):
    # Filter the master data based on regions in the request
    filtered_data = [
        item for item in telemetry_data if item["region"] in request.regions
    ]

    if not filtered_data:
        return {}

    # Group the filtered data by region
    grouped_data = {}
    for record in filtered_data:
        region = record["region"]
        if region not in grouped_data:
            grouped_data[region] = {"latencies": [], "uptimes": []}
        
        grouped_data[region]["latencies"].append(record["latency_ms"])
        grouped_data[region]["uptimes"].append(record["uptime_status"])

    # Calculate metrics for each region
    results = {}
    for region, data in grouped_data.items():
        latencies = np.array(data["latencies"])
        uptimes = np.array(data["uptimes"])

        results[region] = {
            "avg_latency": np.mean(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "avg_uptime": np.mean(uptimes),
            "breaches": int(np.sum(latencies > request.threshold_ms))
        }
    
    return results

@app.get("/")
def read_root():
    return {"message": "eShopCo Telemetry Service"}
