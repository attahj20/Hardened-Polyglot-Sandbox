import time
import json
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from redis import Redis
from config import AnalyticsConfig

app = FastAPI(title="Event-Driven Analytics Aggregator Ingestion API")

# Setup our Redis storage client
redis_client = Redis(
    host=AnalyticsConfig.REDIS_HOST, 
    port=AnalyticsConfig.REDIS_PORT, 
    db=0, 
    decode_responses=True
)

class MetricPayload(BaseModel):
    metric_name: str = Field(..., description="Type of metric being recorded")
    value: float = Field(..., description="Numerical telemetry value")

@app.post("/api/v1/metrics", status_code=status.HTTP_201_CREATED)
async def ingest_metric(payload: MetricPayload):
    """Ingests inbound real-time telemetry markers into a Redis Sorted Set."""
    if payload.metric_name not in AnalyticsConfig.METRIC_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric. Must be one of {AnalyticsConfig.METRIC_TYPES}"
        )
    
    current_time = time.time()
    data_packet = {
        "metric_name": payload.metric_name,
        "value": payload.value,
        "timestamp": current_time
    }
    
    try:
        # Use Redis ZADD: score is timestamp, value is stringified JSON payload
        # We append a unique suffix to the value string so identical metrics don't overwrite each other
        unique_value = f"{json.dumps(data_packet)}::{current_time}"
        redis_client.zadd(AnalyticsConfig.METRICS_ZSET_KEY, {unique_value: current_time})
        
        return {"status": "INGESTED", "metric": payload.metric_name, "timestamp": current_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Broker insertion failure: {str(e)}")

@app.get("/health")
async def health():
    try:
        redis_client.ping()
        return {"status": "ONLINE"}
    except Exception:
        return {"status": "OFFLINE"}
