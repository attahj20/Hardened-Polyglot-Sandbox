# Project 5: Real-Time Event-Driven Analytics Aggregator (EDAA)

A decoupled, high-throughput telemetry pipeline built with **Python**, **Redis Sorted Sets (ZSET)**, and **FastAPI WebSockets**. EDAA ingests high-velocity event streams, maintains a self-cleaning 60-second sliding window in memory, computes real-time statistical aggregates, and broadcasts live snapshots to connected clients with sub-second latency.

---

## Architecture Overview

To prevent database lock contention and client-induced CPU spikes, EDAA separates ingestion, computation, and delivery into three independent layers:

```text
+-------------------+       ZADD (score=timestamp)       +-----------------------+

|  Traffic Producer | ---------------------------------> |  Redis Sorted Set     |
| (mock_traffic.py) |    payload::<microsecond_ts>       |  (60s Sliding Window) |
+-------------------+                                    +-----------+-----------+
                                                                     |
                                                    ZREMRANGEBYSCORE & ZRANGEBYSCORE
                                                                     v
+-------------------+       GET aggregated_stats         +-----------------------+

| WebSocket Server  | <--------------------------------- |  Aggregation Engine   |
|    (stream.py)    |       SET aggregated_stats         |      (engine.py)      |
+---------+---------+                                    +-----------------------+
          |
          |  ws://127.0.0.1:8000/ws/analytics (1s tick)
          v
+-------------------+

|  Live Consumer    |
|  (ws_client.py)   |
+-------------------+
```

### Key Design Decisions
* **O(log N) Sliding Window (`engine.py`):** Uses Redis Sorted Sets scored by Unix epoch timestamps. Every second, `ZREMRANGEBYSCORE` evicts stale events older than 60 seconds while `ZRANGEBYSCORE` extracts active metrics for aggregation.
* **Collision-Free Cardinality (`mock_traffic.py`):** Redis ZSETs enforce member uniqueness. Appending a `::<timestamp>` suffix to each serialized JSON packet prevents identical metric readings from overwriting each other during traffic bursts.
* **Decoupled Fan-Out (`stream.py`):** Heavy window math executes once per second inside a single background daemon rather than inside individual WebSocket connection loops, allowing hundreds of concurrent listeners without multiplying compute overhead.

---

## Directory Structure

```text
project5_analytics/
├── config.py          # Centralized Redis keys, window duration, and metric schemas
├── engine.py          # Sliding-window pruning and statistical aggregation daemon
├── stream.py          # Asynchronous FastAPI WebSocket broadcaster (/ws/analytics)
├── mock_traffic.py    # High-frequency telemetry generator with simulated latency spikes
├── ws_client.py       # Terminal WebSocket consumer for live stream verification
├── test_engine.py     # Deterministic pytest suite mocking Redis ZSET operations
└── README.md          # Project documentation and benchmark metrics
```

---

## Quick Start

### 1. Start Redis Infrastructure
Launch a lightweight Redis container on port `6379`:
```bash
docker run -d --name edaa-redis -p 6379:6379 redis:alpine
```

### 2. Install Python Dependencies
Create and activate a virtual environment, then install the required packages:
```bash
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn websockets redis pytest
```

### 3. Launch the Pipeline Services
Open four terminal sessions inside `project5_analytics/` with your virtual environment active:

* **Terminal 1 — Sliding-Window Processing Engine:**
  ```bash
  python engine.py
  ```
* **Terminal 2 — FastAPI WebSocket Server:**
  ```bash
  python -m uvicorn stream:app --host 127.0.0.1 --port 8000 --reload
  ```
* **Terminal 3 — High-Volume Traffic Generator:**
  ```bash
  python mock_traffic.py
  ```
* **Terminal 4 — Live WebSocket Stream Consumer:**
  ```bash
  python ws_client.py
  ```

---

## Sample Live Output & Verified Benchmarks

Under continuous micro-batch ingestion (5–25 packets per 0.5s tick), the engine sustains **~1,750 active events** inside the 60-second rolling window while pruning ~30 expired records per second:

```json
{
  "window_meta": {
    "window_size_sec": 60,
    "recalculated_at": 1794805679.382113,
    "total_active_events": 1760
  },
  "metrics": {
    "cpu_utilization": {
      "event_count": 582,
      "moving_average": 115.23,
      "max_value_spike": 1170.36
    },
    "clickstream_event": {
      "event_count": 575,
      "moving_average": 100.93,
      "max_value_spike": 1100.19
    },
    "transaction_value": {
      "event_count": 603,
      "moving_average": 110.8,
      "max_value_spike": 1132.3
    }
  }
}
```

---

## Running Unit Tests

The test suite mocks Redis ZSET calls via `unittest.mock` to validate moving averages, spike detection, and empty-window zero-division guards without external dependencies:

```bash
pytest test_engine.py -v
```
