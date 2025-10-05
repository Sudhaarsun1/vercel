# api/index.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import numpy as np

# --- 1. Initialize FastAPI app ---
app = FastAPI()


# --- 2. Enable CORS ---
# This middleware will allow POST requests from any origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods, including POST
    allow_headers=["*"],  # Allows all headers
)


# --- 3. Define Pydantic Models for Request Body Validation ---
# This model represents a single data point in the "regions" list.
class RegionData(BaseModel):
    region: str
    latency_ms: int
    uptime_status: bool  # True for up, False for down

# This is the main model for the entire request body.
class MetricsRequest(BaseModel):
    regions: List[RegionData]
    threshold_ms: int


# --- 4. Define the POST Endpoint for Metrics Calculation ---
@app.post("/metrics")
def calculate_metrics(request: MetricsRequest):
    """
    Accepts a list of regional data points and a latency threshold,
    then calculates and returns key metrics for each region.
    """
    if not request.regions:
        return {}

    # Group data by region name
    grouped_data = {}
    for record in request.regions:
        if record.region not in grouped_data:
            grouped_data[record.region] = {"latencies": [], "uptimes": []}
        
        grouped_data[record.region]["latencies"].append(record.latency_ms)
        grouped_data[record.region]["uptimes"].append(record.uptime_status)

    # Calculate metrics for each region
    results = {}
    for region, data in grouped_data.items():
        latencies = np.array(data["latencies"])
        uptimes = np.array(data["uptimes"])

        results[region] = {
            "avg_latency": np.mean(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "avg_uptime": np.mean(uptimes),  # Mean of bools (True=1, False=0) gives the uptime ratio
            "breaches": int(np.sum(latencies > request.threshold_ms)) # Count where latency > threshold
        }
    
    return results


# --- Original root endpoint (optional) ---
@app.get("/")
def read_root():
    return {"message": "Metrics API is running. Use the /metrics endpoint with a POST request."}
