# Designing Backpressure-Safe WebSocket Streams with FastAPI and Redis

Connecting a live frontend dashboard directly to an analytics computation loop is one of the fastest ways to crash a backend service under load.

In naive WebSocket architectures, every connected client triggers its own aggregation query inside a `while True` loop. When 500 operators open the monitoring dashboard during an incident, your backend executes 500 identical window scans every second—multiplying CPU load right when the system is already stressed.

While building the **Event-Driven Analytics Aggregator (EDAA)**, I eliminated this bottleneck by decoupling **window computation** from **client fan-out**.

---

## The Three-Stage Decoupled Pipeline

Instead of letting WebSocket handlers compute metrics, the architecture splits responsibilities across three isolated components:

### 1. High-Velocity Ingestion (`mock_traffic.py`)
Producers serialize telemetry packets and push them straight into a Redis Sorted Set (`ZADD`). Producers never wait for downstream calculations or connected clients.

### 2. Single-Writer Compute Daemon (`engine.py`)
An independent background worker runs on a deterministic 1-second tick:
* Purges expired records outside the 60-second boundary (`ZREMRANGEBYSCORE`).
* Computes counts, moving averages, and maximum spikes across active records.
* Writes a single pre-computed JSON snapshot back to Redis (`SET aggregated_stats`).

### 3. Stateless WebSocket Broadcaster (`stream.py`)
FastAPI exposes an asynchronous `/ws/analytics` endpoint. Each connected client loop simply reads the pre-computed JSON snapshot from Redis (`GET aggregated_stats`) and pushes it down the socket:

```python
@app.websocket("/ws/analytics")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            latest_stats_raw = redis_client.get(AnalyticsConfig.AGGREGATED_STATS_KEY)
            if latest_stats_raw:
                await websocket.send_json(json.loads(latest_stats_raw))
            await asyncio.sleep(AnalyticsConfig.ENGINE_TICK_RATE_SEC)
    except WebSocketDisconnect:
        pass
```

---

## Why This Scales

Whether **1 client** or **1,000 clients** connect to `/ws/analytics`, the sliding-window aggregation math executes **exactly once per second**. Redis absorbs the lightweight `GET` reads in microseconds, while FastAPI's async event loop handles concurrent socket I/O without blocking.

---

## Key Takeaway

Real-time streaming systems stay resilient when state calculation and network delivery are isolated. Pre-compute your snapshots once, cache them at the edge of your memory store, and let your WebSocket layer focus strictly on non-blocking delivery.
