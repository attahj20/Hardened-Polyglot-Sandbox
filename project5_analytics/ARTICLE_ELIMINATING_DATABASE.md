# Eliminating Database Lock Contention in Live Dashboards Using Redis Sorted Sets

Every fast-growing engineering team hits the same operational wall: a real-time analytics dashboard that works cleanly in staging suddenly brings the primary database to its knees in production.

The culprit is almost always the same pattern—polling a relational database every second with rolling-window queries:

```sql
SELECT metric_name, AVG(value), MAX(value), COUNT(*)
FROM telemetry_events
WHERE created_at >= NOW() - INTERVAL '60 seconds'
GROUP BY metric_name;
```

When 10 dashboard users refresh simultaneously alongside thousands of incoming write events, PostgreSQL or MySQL spends its I/O budget scanning indexes, acquiring row locks, and thrashing buffer pools for ephemeral data that loses relevance 60 seconds later.

To solve this, I built the **Event-Driven Analytics Aggregator (EDAA)**—an in-memory sliding-window telemetry pipeline powered by **Redis Sorted Sets (ZSET)** and **Python**.

---

## Why Redis Sorted Sets Fit Sliding Windows Naturally

Unlike relational tables where time-range pruning requires heavy `DELETE` sweeps and vacuuming, a Redis Sorted Set stores unique string members ordered by a 64-bit floating-point **score**.

By assigning the Unix epoch timestamp (`time.time()`) as the score during ingestion, the data structure automatically stays sorted chronologically:

1. **O(log N) Ingestion (`ZADD`):** Producers push telemetry events into the set without table locks.
2. **O(log N + M) Eviction (`ZREMRANGEBYSCORE`):** The processing engine deletes all records older than `current_time - 60` in a single atomic sweep.
3. **O(log N + K) Window Extraction (`ZRANGEBYSCORE`):** Only the active 60-second slice is pulled into Python memory for aggregation.

---

## Live Benchmark Results

Under simulated high-velocity traffic (5–25 telemetry packets dispatched every 0.5 seconds), the engine sustained **~1,750 active events** inside the 60-second rolling window while continuously evicting ~30 stale records per second:

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

## Key Takeaway

Relational databases belong to durable systems of record. When your workload requires sub-second rolling metrics over hot operational data, moving the sliding window into Redis Sorted Sets eliminates lock contention and drops aggregation latency to milliseconds.

*Explore the full source code and unit tests in my `Hardened Polyglot Sandbox` repository (`project5_analytics/`).*
